from flask import Flask, Response, request, render_template
import time
import json
import os
import threading
import markdown

# import settings
import archivist.configs.settings as settings
from archivist.nodes.node_handler import NODE_REGISTRY, import_nodes
from archivist.webui.workflow_manager import Workflow, running_workflow
from modules.message_manager import Conversation, Message_Node
from archivist.webui.agent import Agent # Placeholder
from llama_server_controller import LlamaServerController
from model import Model

from archivist.webui.agent_tab import agent_bp

app = Flask(__name__,
            template_folder="../archivist/templates",
            static_folder="../archivist/static"
            )

app.register_blueprint(agent_bp, url_prefix="/agent")

current_conv = Conversation()
controller = None

def init_controller():
    global controller
    PORT_NUM = 5001
    llama_server_path = os.path.join(settings.LLAMA_CPP_DIR, "llama-server")
    controller = LlamaServerController(llama_server_path, PORT_NUM)

    # Settings
    model_path = os.path.join(settings.LLMS_DIR, "Qwen3-30B-A3B-Instruct-2507-UD-Q4_K_XL.gguf")
    devices = "Vulkan0,Vulkan1"

    controller.run(False, model_path, devices)

def health_check():
    global controller
    try:
        if controller is not None:
            while controller.get_health() != 200:
                print("Waiting for controller to be ready...")
                time.sleep(2)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        os._exit(0)

def init_model():
    global controller, model, Archivist_settings, conversation_history, Archivist_instruct

    # Initialize model and agent
    model = Model()
    role_name = "Archivist"
    Archivist = Agent(role_name)
    Archivist_settings = Archivist.get_role_settings()
    Archivist_instruct = Archivist.get_role_instruct()

    # Initial conversation history
    conversation_history = []
    conversation_history.append({"role": "system", "content": Archivist_instruct})

@app.route("/")
def home():
    return render_template("main.html")
        
# response stream from agent node is prob not in the right format right for json and previous assumptions
@app.route("/stream", methods=["POST"])
def stream():
    data = request.json

    # run workflow set by user
    workflow = Workflow()
    workflow.load_workflow_file("Archivist") # placeholder
    workflow.convert_to_nodes()
    workflow.get_node_tree()
    workflow.map_node_to_func(NODE_REGISTRY)

    # template for on_message
    # address is left as empty string intentionally
    # response stream from agent.py will fill it in
    on_message_data = {"message": data["text"], "address": "", "msg_type": "stream"} 

    trigger_inputs = {"trigger_events.on_message.on_message": on_message_data}
    response_stream = workflow.call_funcs(workflow.func_tree, trigger_inputs)
    return Response(response_stream, mimetype="application/json")

@app.route("/get_chat_list", methods=["GET"])
def get_chat_list():
    conv_list = os.listdir(settings.MEMORY_DIR)
    data = []
    for conv_id in conv_list:
        data.append({"id": conv_id[:-5]})

    return Response(json.dumps(data), mimetype="application/json")

@app.route("/load_chat/<chat_id>", methods=["GET"])
def load_chat(chat_id):
    global current_conv, conversation_history
    if (not current_conv.is_empty()):
        current_conv.save()

    memory = os.path.join(settings.MEMORY_DIR, chat_id + ".json")
    current_conv.load(memory)
    conversation_history[:1]

    with open(memory, "r") as file:
        json_data = json.load(file)

    return Response(json.dumps(json_data), mimetype="application/json")

@app.route("/new_chat", methods=["GET"])
def new_chat():
    global current_conv, conversation_history
    current_conv.save()
    current_conv = Conversation()
    conversation_history = []
    conversation_history.append({"role": "system", "content": Archivist_instruct})

    return Response(json.dumps({"id": current_conv.conv_id}), mimetype="application/json")

if __name__ == "__main__":
    # init_model()

    # t = threading.Thread(target=init_controller)
    # t.start()

    # health_check()

    import_nodes()

    app.run(host="0.0.0.0", port=5000)
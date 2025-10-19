from flask import Flask, Response, request, render_template
import time
import json
import os
import threading
import markdown

import settings
from modules.message_manager import Conversation, Message_Node
from llama_server_controller import LlamaServerController
from model import Model
from webui.agent import Agent # Placeholder

from nodes.trigger_events.on_message import on_message

from webui.agent_tab import agent_bp

app = Flask(__name__)
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

def response_stream(user_address):
    """
    A generator function that yields the LLM output along with the markdown version.
    \n\tFirst yield is the user address
    \n 2nd - nth yield is text in a token chunk
    \n next yield is the markdown version
    \n last yield is the assistant address

    """
    global conversation_history, controller, model, Archivist_settings, current_conv, Archivist_instruct

    yield json.dumps({"type":"user_address", "value":user_address}) + "\n"
    model_message = ""

    # Stream the LLM response by token
    for message_data, is_last in model.generate_stream(conversation_history, controller, Archivist_settings):
        if is_last:
            yield json.dumps({"type":"final", "value":markdown.markdown(model_message)}) + "\n"
            break
        yield json.dumps({"type":"message", "value": message_data}) + "\n"
        model_message += message_data

    # Keep track of the conversation
    conversation_history.append({"role": "assistant", "content": model_message})
    temp_message = Message_Node("Archivist", "Assistant", model_message, instruct=Archivist_instruct)
    assistant_address = current_conv.add_message(temp_message, user_address)

    yield json.dumps({"type":"assistant_address", "value":assistant_address}) + "\n"

    if (not current_conv.find_conversation()):
        current_conv.save()

# @app.route("/stream", methods=["POST"])
# def stream():
#     global current_conv, conversation_history
#     data = request.json
#     text = data.get("text", "")

#     conversation_history.append({"role": "user", "content": text})
#     temp_message = Message_Node("user", "User", text, "")
#     # TODO: Change to dynamic address
#     user_address = current_conv.add_message(temp_message, "0"*(len(conversation_history)-2))
    
#     return Response(response_stream(user_address), mimetype="application/json")

@app.route("/stream", methods=["POST"])
def stream():
    pass


@app.route("/save_edit_stream", methods=["POST"])
def save_edit_stream():
    global current_conv, conversation_history

    data = request.json
    text_input = data.get("text", "")
    message_address = data.get("address", "")
    parent_address = message_address[:len(message_address)-1]

    new_message = Message_Node("user", "User", text_input)
    new_message_address = current_conv.add_message(new_message, parent_address)

    conv_list = current_conv.get_conv_list_from_address(new_message_address)
    conversation_history = conversation_history[:1]

    for i in range(len(conv_list)):
        message = {
            "role":conv_list[i].role,
            "content":conv_list[i].text
        }
        conversation_history.append(message)

    return Response(response_stream(message_address), mimetype="application/json")

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

    app.run(host="0.0.0.0", port=5000)
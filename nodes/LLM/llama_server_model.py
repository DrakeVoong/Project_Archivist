import os
import threading
import sys
import time

from llama_server_controller import LlamaServerController
from modules.message_manager import Message_Node, Conversation
import archivist.configs.settings as settings
from nodes.node_handler import node

controller = None
output_file_name = None


@node(inputs=None, settings=["port", "log_file", "model_path", "devices"], outputs=["controller", "output_file"])
def initalize_llama_server(port: int, log_file: str, model_name: str, devices: str) -> tuple[LlamaServerController, str]:
    global controller, output_file_name

    if controller != None:
        return controller, output_file_name

    PORT_NUM = port
    output_file = os.path.join(settings.MAIN_DIR, log_file)
    llama_server_path = os.path.join(settings.LLAMA_CPP_DIR, "llama-server")
    model_path = os.path.join(settings.LLMS_DIR, model_name)
    llama_controller = LlamaServerController(llama_server_path, PORT_NUM)

    t = threading.Thread(target=llama_controller.run, args=(False, model_path, devices), daemon=True)
    t.start()

    try:
        while llama_controller.get_health() != 200:
            print("Waiting for controller to be ready...")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(0)

    controller = llama_controller
    output_file_name = output_file

    return llama_controller, output_file
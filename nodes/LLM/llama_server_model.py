import os
import threading

from llama_server_controller import LlamaServerController
from modules.message_manager import Message_Node, Conversation
import settings
from nodes.node_handler import node


@node(inputs=None, settings=["port", "log_file"], outputs=["controller", "output_file"])
def initalize_llama_server(port: int, log_file: str, model_path: str, devices: str) -> tuple[LlamaServerController, str]:
    PORT_NUM = port
    output_file = os.path.join(settings.MAIN_DIR, log_file)
    llama_server_path = os.path.join(settings.LLAMA_CPP_DIR, "llama-server")
    controller = LlamaServerController(llama_server_path, PORT_NUM)

    t = threading.Thread(target=controller.run, args=(False, model_path, devices))
    t.start()

    return controller, output_file
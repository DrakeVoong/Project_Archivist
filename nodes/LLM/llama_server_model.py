import os

from llama_server_controller import LlamaServerController
from modules.message_manager import Message_Node, Conversation
import settings
from nodes.node_handler import node

@node(inputs=None, settings=["port", "log_file"], outputs=["controller", "output_file"])
def initalize_llama_server(port: int, log_file: str) -> tuple[LlamaServerController, str]:
    PORT_NUM = port
    output_file = os.path.join(settings.MAIN_DIR, "llama_server_log.txt")
    llama_server_path = os.path.join(settings.LLAMA_CPP_DIR, "llama-server")
    controller = LlamaServerController(llama_server_path, PORT_NUM)

    return controller, output_file

@node(inputs=["message", "address", "conv", "controller", "response_type"], settings=["generation_settings"], outputs=["response"])
def stream_response(message:str, address:str, conv: Conversation, controller: LlamaServerController, response_type: str, generation_settings: dict):
    if response_type == "send":
        user_message = Message_Node("user", "User", message, "")
    pass

    
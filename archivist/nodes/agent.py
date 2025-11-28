import os
import json
import markdown
from typing import Generator

import archivist.configs.settings as settings
from archivist.message_manager import Message_Node, Conversation
from archivist.nodes.node_handler import node
from model import Model
from llama_server_controller import LlamaServerController

conv_history = []
controller = None
model = Model()
agent_settings = []
conv = None
agent_instruct = {}

def response_stream(user_address):
    global conv_history, controller, model, conv, agent_settings, agent_instruct

    yield json.dumps({"type":"user_address", "value":user_address}) + "\n"
    model_message = ""

    # Stream the LLM response by token
    for message_data, is_last in model.generate_stream(conv_history, controller, agent_settings):
        if is_last:
            yield json.dumps({"type":"final", "value":markdown.markdown(model_message)}) + "\n"
            break
        yield json.dumps({"type":"message", "value": message_data}) + "\n"
        model_message += message_data

    # Keep track of the conversation
    conv_history.append({"role": "assistant", "content": model_message})
    temp_message = Message_Node("Archivist", "Assistant", model_message, instruct=agent_instruct)
    assistant_address = conv.add_message(temp_message, user_address)

    yield json.dumps({"type":"assistant_address", "value":assistant_address}) + "\n"

    if (not conv.find_conversation()):
        conv.save()

@node(settings=["agent_instruct", "max_length", "temperature", "top_p", "top_k", "min_p", "frequency_penalty", "presence_penalty"],
        outputs=["agent_info"])
def load_agent_info(agent_instruct: str, max_length: int, temperature: int, 
                top_p: int, top_k: int, min_p: int, frequency_penalty: int, presence_penalty: int) -> tuple[dict]:
    agent_settings = {
        "max_length": max_length,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "min_p": min_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty
    }

    agent_info = {
        "agent_instruct": agent_instruct,
        "agent_settings": agent_settings
    }

    return agent_info

@node(inputs=["message", "address", "type", "llama_controller", "conversation_history", "conversation", "agent_info"], outputs=["stream_response"])
def agent(message: str, address: str, type:str, llama_controller:LlamaServerController, conversation_history: list, conversation: Conversation, agent_info: dict) -> tuple[Generator]:
    global conv, conv_history, agent_settings, agent_instruct, controller

    controller = llama_controller
    
    # First time user is sending a message in the conversation
    if conv_history == []:
        conv_history = conversation_history
        conv = conversation

    agent_settings = agent_info["agent_settings"]
    agent_instruct = agent_info["agent_instruct"]

    # Webui live response
    if type == "stream":
        conv_history.append({"role": "user", "content": message})
        msg_node = Message_Node("user", "User", message, "")
        user_address = conv.add_message(msg_node, address)

        return response_stream(user_address)
import os
import time
import sys

import threading
from llama_server_controller import LlamaServerController
from model import Model
from modules.message_manager import Conversation, Message_Node
from agent import Agent
import settings

# Initialize llama-server
PORT_NUM = 5001
llama_server_path = os.path.join(settings.LLAMA_CPP_DIR, "build", "bin", "Release", "llama-server")
controller = LlamaServerController(llama_server_path, PORT_NUM)

# Initialize model and agent
model = Model()
role_name = "Archivist"
Archivist = Agent(role_name)
Archivist_instruct = Archivist.get_role_instruct()
Archivist_settings = Archivist.get_role_settings()

def main():
    # Wait until llama-server/kobold is ready
    try:
        while controller.get_health() != 200:
            print("Waiting for controller to be ready...")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(0)

    # Initialize conversation
    conversation_history = []
    conversation_history.append({"role": "system", "content": Archivist_instruct})
    conversation = Conversation()

    # Conversation loop
    while True:
        # User's turn
        message = input("User: ")
        conversation_history.append({"role": "user", "content": message})
        temp_message = Message_Node("user", "User", message, "")
        conversation.add_message(temp_message, "0"*(len(conversation_history)-2))
        model_message = ""

        # stream printing of model response
        for message_data, is_last in model.generate_stream(conversation_history, controller, Archivist_settings):
            if is_last:
                print("\n")
                print(message_data)
                total_token = message_data
                break
            print(message_data, end="", flush=True)
            model_message += message_data
        print("\n")

        # Saving assistant's response
        conversation_history.append({"role": "assistant", "content": model_message})
        temp_message = Message_Node("Archivist", "Assistant", model_message, "", instruct=Archivist_instruct)
        conversation.add_message(temp_message, "0"*(len(conversation_history)-2))
        conversation.save()


    controller.terminate()

# Settings
model_path = os.path.join(settings.LLMS_DIR, "Qwen3-30B-A3B-Instruct-2507-UD-Q4_K_XL.gguf")
devices = "cuda0,cuda1"

# Run llama-server
thread1 = threading.Thread(target=controller.run, args=(False, model_path, devices)) 
thread2 = threading.Thread(target=main)

thread1.start()
thread2.start()

thread1.join()
thread2.join()

print("Program finished")
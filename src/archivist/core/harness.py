import time

from archivist.core.agent import Agent
from archivist.core.conversation import Conversation
from archivist.core.exceptions import TimeoutError
from archivist.core.message import Message, MessageNode, ContentType, UserMessage, AssistantMessage, SystemMessage
from archivist.LLM_providers.llamacpp_server import LlamaCPPServer
from archivist.LLM_providers.serialize import convert_to_openai
from archivist.storage.SQLite import SQLDB

def build_context(conversation:Conversation, agent:Agent) -> list[dict[str, str]]:
    message_nodes = conversation.get_message_chain()

    # Create system message
    system_content = ContentType(agent.system_instruct)
    system_message = SystemMessage("system", system_content)
    system_message = convert_to_openai(system_message)

    messages = [system_message]
    for message_node in message_nodes:
        messages.append(convert_to_openai(message_node.message))

    return messages

def add_and_save(message:Message, conversation:Conversation, db:SQLDB):
    node = conversation.append(message)
    db.insert_message_node(node, conversation)
    return node


config = [
    "-fa", "1",
    "--fit-target", "128",
    "--fit-ctx", "65536"
]

# How long to wait for llama.cpp startup in seconds
TIMEOUT = 15

def main():
    llama_cpp = LlamaCPPServer("5002")
    llama_cpp.connect_model("Qwen3.6-35B-A3B-UD-Q4_K_M.gguf", config)

    start = time.time()
    while llama_cpp.get_status() != 200:
        time.sleep(1)
        if time.time() - start >= TIMEOUT:
            raise TimeoutError(f"llama.cpp server did not start in {TIMEOUT} seconds.")


    DB = SQLDB()
    CLaRA = Agent("CLaRA") # primary agent
    convo = Conversation()

    user_name = "User"

    while(True):
        print(f"{user_name}: ")
        user_response = input()
        user_content = ContentType(user_response)
        user_message = UserMessage(user_name, user_content)
        user_node = add_and_save(user_message, convo, DB)


        context = build_context(convo, CLaRA)
        response = llama_cpp.generate(context)
        agent_response = response["choices"][0]["message"]["content"]

        print(f"{CLaRA.name}: {agent_response}")

        agent_content = ContentType(agent_response)
        agent_message = AssistantMessage(CLaRA.name, agent_content, response["model"], response["choices"][0]["finish_reason"])
        agent_node = add_and_save(agent_message, convo, DB)

if __name__ == "__main__":
    main()
import time
from openai.types.chat import ChatCompletionMessageParam

from archivist.core.agent import Agent
from archivist.core.conversation import Conversation
from archivist.core.exceptions import TimeoutError
from archivist.core.message import Message, Content, UserMessage, AssistantMessage, SystemMessage, ToolMessage
from archivist.llm_providers.llamacpp_server import LlamaCPPServer
from archivist.llm_providers.serialize import convert_to_openai
from archivist.storage.SQLite import SQLDB

def build_context(conversation:Conversation, agent:Agent) -> list[ChatCompletionMessageParam]:
    message_nodes = conversation.get_message_chain()

    # Create system message
    system_content = Content(agent.system_instruct)
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

# -- Defining Tools

tools = [{
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two numbers",
        "parameters": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
    },
}]


config = [
    "-fa", "1",
    "--fit-target", "128",
    "--fit-ctx", "8192",
    "-np", "1",
]

# How long to wait for llama.cpp startup in seconds
TIMEOUT = 30

def main():
    llama_cpp = LlamaCPPServer("5002")
    llama_cpp.connect_model("Qwen3.6-35B-A3B-UD-Q4_K_M.gguf", config)

    # Wait for llama-server to start
    start = time.time()
    while llama_cpp.get_status() != 200:
        time.sleep(1)
        if time.time() - start >= TIMEOUT:
            raise TimeoutError(f"llama.cpp server did not start in {TIMEOUT} seconds.")

    # Define database, main agent, and conversation
    db = SQLDB()
    CLaRA = Agent("CLaRA") # primary agent
    conv = Conversation()

    user_name = "User"

    while(True):
        # User Message
        print(f"{user_name}: ")
        user_response = input()
        user_content = Content(user_response)
        user_message = UserMessage(user_name, user_content)
        add_and_save(user_message, conv, db)

        context = build_context(conv, CLaRA) # build llm input using CLaRA system instruct
        response = llama_cpp.generate_openai(context, tools)

        print(response)
        # llm response text
        agent_response = response.choices[0].message.content

        if agent_response is None:
            raise ValueError()

        print(f"{CLaRA.name}: {agent_response}")
        
        agent_content = Content(agent_response)
        agent_message = AssistantMessage(CLaRA.name, agent_content, response.model, response.choices[0].finish_reason)
        add_and_save(agent_message, conv, db)

if __name__ == "__main__":
    main()
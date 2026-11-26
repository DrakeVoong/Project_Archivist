import time
from openai.types.chat import ChatCompletionMessageParam
import json
import argparse
from pathlib import Path

from archivist.core.agent import Agent
from archivist.core.conversation import Conversation
from archivist.core.exceptions import TimeoutError
from archivist.core.type import Message, Content, UserMessage, AssistantMessage, SystemMessage, ToolMessage, ToolCall
from archivist.llm_providers.llamacpp_server import LlamaCPPServer
from archivist.llm_providers.serialize import convert_to_openai
from archivist.storage.SQLite import SQLDB
from archivist.core.tool import call_tool, get_tools
from archivist.config.settings import CONV_PATH, LOG_PATH

def build_context(conversation:Conversation, agent:Agent) -> list[ChatCompletionMessageParam]:
    """
    The system prompt/context is rebuilt every conversation so switching models is simple
    """
    message_nodes = conversation.get_message_chain()

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

def command_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dev", action="store_true", help="enable dev mode")
    args = parser.parse_args()

    if args.dev:
        print("Dev mode on")
        print("Cleaning leftover files.")

        files = [
            CONV_PATH / "conversations.db",
            LOG_PATH / "llama_server_log.txt",
        ]

        for file in files:
            Path(file).unlink(missing_ok=True)


# llama-server can take a while loading a model on local hardware
TIMEOUT = 30

def main():
    command_arguments()

    llama_cpp = LlamaCPPServer("5002")
    llama_cpp.connect_model("Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")

    start = time.time()
    while llama_cpp.get_status() != 200:
        time.sleep(1)
        if time.time() - start >= TIMEOUT:
            raise TimeoutError(f"llama.cpp server did not start in {TIMEOUT} seconds.")

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

        # build llm input using CLaRA system instruct
        context = build_context(conv, CLaRA)
        response = llama_cpp.generate_openai(context, CLaRA.sampling, get_tools())

        agent_response = response.choices[0].message.content

        if agent_response is None:
            agent_response = ""

        # agent loop - keep going until the model stops requesting tool calls
        # the model decides when to finish with "stop"
        while response.choices[0].finish_reason == "tool_calls":

            raw_tool_calls = response.choices[0].message.tool_calls
            if not raw_tool_calls:
                raise ValueError("Response indicated tool calls but provided none.")

            # Convert openai tool_call type to ToolCall type
            # So that the code does not depend on a openai API format
            tool_calls = []
            for tool_call in raw_tool_calls:
                if tool_call.type != "function":
                    raise ValueError("Unsupported custom tool call.")
                tool_calls.append(ToolCall(tool_call.id, tool_call.function.name, tool_call.function.arguments))

            # Append agent tool call to conversation and db
            agent_content = Content(agent_response)
            agent_message = AssistantMessage(CLaRA.name, 
                                             agent_content, 
                                             getattr(response.choices[0].message, "reasoning_content", None), 
                                             response.model, 
                                             response.choices[0].finish_reason, 
                                             tuple(tool_calls)
                                             )
            add_and_save(agent_message, conv, db)

            # Call each function that corresponds to a tool call
            # then add to conversation and db
            for tool_call in raw_tool_calls:
                if tool_call.type == "function":
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    tool_call_id = tool_call.id
                    tool_content = Content(call_tool(name, args))
                    tool_message = ToolMessage(name, tool_content, tool_call_id)
                    add_and_save(tool_message, conv, db)

            # build llm input using CLaRA system instruct and generate response
            # that could be tool call or final response to user
            context = build_context(conv, CLaRA)
            response = llama_cpp.generate_openai(context, CLaRA.sampling, get_tools())
            agent_response = response.choices[0].message.content

            if agent_response is None:
                agent_response = ""

        # The last message is to the user (in the tool call loop)
        print(f"{CLaRA.name}: {agent_response}")

        agent_content = Content(agent_response)
        agent_message = AssistantMessage(CLaRA.name, 
                                        agent_content, 
                                        getattr(response.choices[0].message, "reasoning_content", None), 
                                        response.model, 
                                        response.choices[0].finish_reason
                                        )
        add_and_save(agent_message, conv, db)

if __name__ == "__main__":
    main()
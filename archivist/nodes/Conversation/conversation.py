from modules.message_manager import Message_Node, Conversation
import archivist.configs.settings as settings
from archivist.nodes.node_handler import node

@node(inputs=["agent_instruct"], outputs=["conversation", "conversation_history"])
def memory(agent_instruct: str) -> tuple[Conversation, list]:
    conversation_history = []
    conversation_history.append({"role": "system", "content": agent_instruct})
    conversation = Conversation()
    conversation_history

    return conversation, conversation_history
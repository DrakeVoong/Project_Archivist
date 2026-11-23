import time
import uuid

from archivist.core.message import MessageNode, Message
from archivist.core.exceptions import EmptyConversationError

class Conversation:

    def __init__(self):
        self.conv_uuid = uuid.uuid4()
        self.time_ns = time.time_ns()
        self.root_messages: list[MessageNode] = [] # root_messages might become depercated in favor of uuid_index
        self.uuid_index: dict[uuid.UUID, MessageNode] = {}
        self.title = ""
        self.active_node:MessageNode | None = None

    @classmethod
    def from_sql(cls):
        pass

    def is_empty(self) -> bool:
        return not self.uuid_index
    
    def get_msg_from_uuid(self, msg_id: uuid.UUID) -> MessageNode | None:
        return self.uuid_index.get(msg_id)

    def append(self, message:Message) -> MessageNode:
        """
        Append a new message into the most recent/follow-up message. (active node)
        """
        node = MessageNode(message, self.active_node)
        if self.active_node:
            self.active_node.children.append(node)

        self._register(node)
        return node

    def branch(self, message: Message, parent: MessageNode) -> MessageNode:
        """Edits/Regeneration of a message"""
        node = MessageNode(message, parent=parent)
        parent.children.append(node)
        self._register(node)
        return node

    def _register(self, node):
        self.uuid_index[node.message.id] = node
        if node.parent is None:
            self.root_messages.append(node)
        self.active_node = node


    def get_message_chain(self) -> list[MessageNode]:
        """Get a single branch of the message tree based on the active message."""
        if self.is_empty():
            msg = "Invalid message. Empty Conversation."
            raise EmptyConversationError(msg, self.conv_uuid)
        
        if self.active_node is None:
            raise ValueError("Active Node is not defined.")

        message_nodes:list[MessageNode] = []
        curr = self.active_node
        while(curr is not None):
            message_nodes.append(curr)
            curr = curr.parent

        message_nodes.reverse()
        return message_nodes

    def print_tree(self):
        """
        Prints the conversation tree.
        """

        if not self.root_messages:
            print("No messages")
            return
        
        # Helper function to recursively print the tree
        def print_tree_helper(curr: MessageNode, level:int):
            name = curr.message.name
            role = type(curr.message)
            print(f"{level * ' '}{name} ({role})")
            for child in curr.children:
                print_tree_helper(child, level + 1)
        
        # Traverse the tree
        for i in range(len(self.root_messages)):
            print_tree_helper(self.root_messages[i], 0)
import time
import uuid
import os

from archivist.core.message import MessageNode, Message
from archivist.core.exceptions import EmptyConversationError

class Conversation:

    def __init__(self):
        self.conv_uuid = uuid.uuid4()
        self.time_ns = time.time_ns()
        self.root_messages: list[MessageNode] = []
        self.uuid_index: dict[uuid.UUID, MessageNode] = {}
        self.title = ""
        self.active_node:MessageNode | None = None

    @classmethod
    def from_sql(cls):
        pass

    def is_empty(self) -> bool:
        return False if len(self.uuid_index) else True
    
    def get_msg_from_uuid(self, msg_id: uuid.UUID) -> MessageNode | None:
        try:
            return self.uuid_index[msg_id]
        except KeyError:
            return None

    def append(self, message:Message) -> MessageNode:
        node = MessageNode(message, self.active_node)
        if self.active_node:
            self.active_node.children.append(node)

        self._register(node)
        return node

    def branch(self, message: Message, parent: MessageNode) -> MessageNode:
        """Edits/Regenerate of messages"""
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

    def get_message_children(self, message_node: MessageNode) -> int:
        
        # Empty Conversation
        if self.is_empty():
            msg = "Invalid message. Empty Conversation."
            raise EmptyConversationError(msg, self.conv_uuid)
        
        return len(self.uuid_index[message_node.message.id].children)

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
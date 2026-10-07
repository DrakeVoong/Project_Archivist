from datetime import datetime
import uuid
import os

from archivist.core.message import MessageNode
from archivist.core.exceptions import MessageUUIDError, EmptyConversationError

class Conversation:

    def __init__(self):
        self.conv_id = uuid.uuid4()
        self._time = datetime.now().timestamp()
        self.root_messages: list[MessageNode] = []
        self.uuid_index: dict[uuid.UUID, MessageNode] = {}
        self.title = ""

    @property
    def time(self):
        return int(self._time * 1000)

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
        
    def add_message(self, message_node: MessageNode, parent_msg_id: uuid.UUID|None = None):

        # Add a new root message
        if parent_msg_id is None:
            self.root_messages.append(message_node)
            self.uuid_index[message_node.message.id] = message_node
            return
            
        # Empty Conversation check with uuid given
        if self.is_empty():
            msg = "Invalid parent message UUID. No inital message in conversation."
            msg += f"\nGot: {parent_msg_id}, Expected: None"
            raise MessageUUIDError(msg, parent_msg_id, self.conv_id)

        parent_node = self.uuid_index[parent_msg_id] 
        parent_node.children.append(message_node)
        message_node.parent = parent_node
        self.uuid_index[message_node.message.id] = message_node

    def get_message_children(self, message_node: MessageNode) -> int:
        
        # Empty Conversation
        if self.is_empty():
            msg = "Invalid message. Empty Conversation."
            raise EmptyConversationError(msg, self.conv_id)
        
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
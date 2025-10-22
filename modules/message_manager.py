from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
import json
import os

import settings 

MEMORY_DIR = settings.MEMORY_DIR

@dataclass
class Message_Node:
    """
    A node in the message tree.

    Attributes:
        name (str): The name of sender.
        role (str): The role of the sender. (User, Assistant, Tool, etc)
        text (str): The text of the message.
        id (str): A uuid4 string. Auto-generated.
        time (str): Time of message in {YYYY-MM-DD HH:MM:SS} format. Auto-generated.
        instruct (Optional[str]): The instruction prompt used by the LLM. Default is None.
        parent (Optional[Message_Node]): The parent node of the message. Default is None.
        children (List[Message_Node]): A list of child nodes of the message. Default is an empty list.
        address (str): The address of the message in the tree in integers. Read left to right with 0 as first index.
                    \n\tFor example, "01" represents the second message of the first message, 
                        "0" represents the first message of the conversation.
    """
    name: str
    role: str
    text: str
    instruct: Optional[str] = None # Instructions for LLM only
    parent: Optional['Message_Node'] = None
    children: List['Message_Node'] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    time: str = field(default_factory=lambda: datetime.now().timestamp())
    address: str = field(default="")

    def to_json(self):
        data = {}
        data["name"] = self.name
        data["role"] = self.role
        data["id"] = self.id
        data["text"] = self.text
        data["time"] = self.time
        data["address"] = self.address
        if self.instruct:
            data["instruct"] = self.instruct
        return data
    
    def __str__(self):
        return (f"Name - {self.name}, Role - {self.role}, id - {self.id},"
                f" text - {self.text}, time - {self.time}, address - {self.address}"
                )


class MessageAddressError(Exception):
    def __init__(self, address: str, reason: str, conv_id: Optional[str] = None):
        self.address = address
        self.reason = reason
        self.conv_id = conv_id
        msg = f"MessageAddressError: '{address}' failed ({reason})"
        if conv_id:
            msg += f" in conversation {conv_id}"
        super().__init__(msg)


class Conversation:
    """
    Stores a conversation between a user and an assistant.

    Attributes:
        messages (List[Message_Node]): A list of Message_Node objects representing the conversation.
        conv_id (str): A uuid4 string representing the conversation id. Auto-generated.
        time (datetime): The time the conversation was created, in unix format. Auto-generated.
        title (str): Name of the conversation. Can be LLM generated or user generated/edited.
    """
    def __init__(self):
        self.messages: List['Message_Node'] = None
        self.conv_id = str(uuid4())
        self.time = datetime.now().timestamp()
        self.title = ""

    def get_message(self, address: str) -> Message_Node:
        """
        Gets a message from the conversation by its address.

        Args:
            address (str): The address of the message in the tree in integers. Read left to right with 0 as first index.
                        \n\tFor example, "01" represents the second message of the first message, 
                            "0" represents the first message of the conversation.

        Returns:
            Message_Node: The message at the specified address.

        Raises:
            MessageAddressError: If there is no message at the specified address or out of range.
        """

        # Conversation must have messages
        if not self.messages: 
            msg = "No messages in conversation"
            raise MessageAddressError(address, msg, self.conv_id)

        # Address must not be empty
        if (len(address) == 0):
            msg = f"Invalid message address. Expected index less than {len(self.messages)}, got empty string."
            raise MessageAddressError(address, msg, self.conv_id)
        
        # Address must be a string of integers
        try:
            idx = int(address[0])
        except (ValueError, TypeError):
            msg = f"Invalid message address. Expected integer, got {address[0]}"
            raise MessageAddressError(address, msg, self.conv_id)

        # Start traversal from the first message
        curr = self.messages[int(address[0])]
        address = address[1:]

        # Traverse the tree
        while len(address) > 0:
            # Address must be a string of integers
            try:
                idx = int(address[0])
            except (ValueError, TypeError):
                msg = f"Invalid message address. Expected integer, got {address[0]}"
                raise MessageAddressError(address, msg, self.conv_id)
            
            # Address must be in range
            if (int(address[0]) >= len(curr.children)):
                msg = f"Invalid message address. Expected index less than {len(curr.children)}, got {int(address[0])}"
                raise MessageAddressError(address, msg, self.conv_id)

            # Continue traversal with child node
            curr = curr.children[int(address[0])]
            address = address[1:]

        return curr

    def add_message(self, message: Message_Node, parent_address: str):
        """
        Adds a message to the conversation at the parent address.

        Args:
            message (Message_Node): The message to add.
            parent_address (str): The address of the parent node in the tree in integers. Read left to right with 0 as first index.
                        \n\tFor example, "01" represents the second message of the first message, 
                            "0" represents the first message of the conversation.

        Raises:

        """
        if not self.messages:
            # Address must be empty if there are no messages
            if (len(parent_address) > 0):
                msg = "Invalid parent address. No inital message in conversation."
                raise MessageAddressError(parent_address, msg, self.conv_id)

            self.messages = []
            message.address = "0"
            self.messages.append(message)
            return message.address

        # Add message to beginning of tree
        if (len(parent_address) == 0):
            message.address = str(len(self.messages))
            self.messages.append(message)
            return message.address

        original_parent_address = parent_address

        # Address must be a string of integers
        try:
            idx = int(parent_address[0])
        except (ValueError, TypeError):
            msg = f"Invalid parent address. Expected integer, got {parent_address[0]}"
            raise MessageAddressError(parent_address, msg, self.conv_id)

        # Start traversal from the first message
        curr = self.messages[int(parent_address[0])]
        parent_address = parent_address[1:]

        # Traverse the tree
        while len(parent_address) > 0:
            # Address must be a string of integers
            try:
                idx = int(parent_address[0])
            except (ValueError, TypeError):
                msg = f"Invalid parent address. Expected integer, got {parent_address[0]}"
                raise MessageAddressError(parent_address, msg, self.conv_id)
            
            # Address must be in range
            if (int(parent_address[0]) >= len(curr.children)):
                msg = f"Invalid parent address. Expected index less than {len(curr.children)}, got {int(parent_address[0])}"
                raise MessageAddressError(parent_address, msg, self.conv_id)

            curr = curr.children[int(parent_address[0])]
            parent_address = parent_address[1:]

        # Found parent node
        # Add message to end of parent node
        message.parent = curr
        message.address = original_parent_address + str(len(curr.children))
        curr.children.append(message)

        return message.address
        
    def delete_message(self, message_address: str):
        """
        Deletes a message from the conversation by its address.

        If the message has children, they will be deleted as well.

        Args:
            message_address (str): The address of the message in the tree in integers. Read left to right with 0 as first index.
                        \n\tFor example, "01" represents the second message of the first message, 
                            "0" represents the first message of the conversation.
        """
        # Conversation must have messages
        if not self.messages:
            msg = "No messages to delete"
            raise MessageAddressError(message_address, msg, self.conv_id)
        
        # Address must be a string of integers
        try:
            idx = int(message_address[0])
        except (ValueError, TypeError):
            msg = f"Invalid message address. Expected integer, got {message_address[0]}"
            raise MessageAddressError(message_address, msg, self.conv_id)

        # Start traversal from the first message
        curr = self.messages[int(message_address[0])]
        message_address = message_address[1:]
        while len(message_address) > 1:
            # Address must be a string of integers
            try:
                idx = int(message_address[0])
            except (ValueError, TypeError):
                msg = f"Invalid message address. Expected integer, got {message_address[0]}"
                raise MessageAddressError(message_address, msg, self.conv_id)
            
            # Address must be in range
            if (int(message_address[0]) >= len(curr.children)):
                msg = f"Invalid message address. Expected index less than {len(curr.children)}, got {int(message_address[0])}"
                raise MessageAddressError(message_address, msg, self.conv_id)
            
            # Continue traversal with child node
            curr = curr.children[int(message_address[0])]
            message_address = message_address[1:]
        
        # Found message
        # Delete message from parent node
        curr.children.pop(int(message_address))

    def get_message_children(self, message_address: str) -> str:
        """
        Get the number of message children in a parent message.

        Returns:
            str: Number of message children
        """
        if not self.messages:
            return ""
        
        if len(message_address) == 1:
            return str(len(self.messages[int(message_address)].children))

        def get_conv_list_helper(curr: Message_Node, level):
            if level < len(message_address)-1:
                get_conv_list_helper(curr.children[int(message_address[level+1])], level+1)
            else:
                return str(len(curr.children))

        get_conv_list_helper(self.messages[int(message_address[0])], 0)

    def get_conv_list(self) -> list[Message_Node]:
        """
        Smushes the conversation into a list of Message_Node objects.

        The list is in the order of the conversation, with the first message being the first element.
        \nThis DOES NOT maintain the tree structure.

        Returns:
            list[Message_Node]: A list of Message_Node objects.
        """
        if not self.messages:
            return []
        
        # Helper function to recursively get the list
        data = []
        def get_conv_list_helper(curr: Message_Node, level):
            data.append(curr.to_json())
            for child in curr.children:
                get_conv_list_helper(child, level+1)

        # Traverse the tree
        for i in range(len(self.messages)):
            get_conv_list_helper(self.messages[i], 0)
        return data
    
    def get_conv_list_from_address(self, address: str) -> list[Message_Node]:
        """
        Gets the list of messages that leads to the address starting from 1st message.

        Returns:
            list[Messsage_Node]: A list of Message_Node objects.
        """
        if not self.messages:
            return []
        
        if len(address) == 1:
            return [self.messages[int(address)]]
        
        conv_list = []

        def get_conv_list_helper(curr: Message_Node, level):
            conv_list.append(curr.to_json())

            if len(address) <= level:
                get_conv_list_helper(curr.children[int(address[level+1])], level+1)

        get_conv_list_helper(self.messages[int(address[0])], 0)

        return conv_list

    def load_json(self, json_data: dict):
        """
        Loads a conversation from a json object.

        Args:
            json_data (dict): The json object to load the conversation from.

        Example:
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "time": "2023-01-01 00:00:00",
            "messages": [
                {
                    "name": "User",
                    "role": "User",
                    "id": "12345678-1234-1234-1234-123456789012",
                    "text": "Hello, how are you?",
                    "time": "2023-01-01 00:00:00",
                    "address": "0"
                },
                {
                    "name": "Assistant",
                    "role": "Assistant",
                    "text": "I'm doing well, thank you!",
                    "time": "2023-01-01 00:00:00",
                    "address": "01"
                }
            ]
        }
        """
        # Load the conversation variables
        self.conv_id = json_data["id"]
        self.time = float(json_data["time"])
        self.messages = []
        self.title = json_data["title"]

        # Helper function to recursively read the json
        def json_to_conversation_helper(curr):
            message = Message_Node(curr["name"], curr["role"], curr["text"], id=curr["id"], time=curr["time"],address=curr["address"])
            if "instruct" in curr:
                message.instruct = curr["instruct"]

            if "children" in curr:
                message.children = []
                for child in curr["children"]:
                    message.children.append(json_to_conversation_helper(child))
            return message

        # Traverse the json
        for message in json_data["messages"]:
            self.messages.append(json_to_conversation_helper(message))

    def print_tree(self):
        """
        Prints the conversation tree.
        """
        if not self.messages:
            print("No messages")
            return
        
        # Helper function to recursively print the tree
        def print_tree_helper(curr, level):
            print(f"{level * ' '}{curr.name} ({curr.role})")
            for child in curr.children:
                print_tree_helper(child, level + 1)
        
        # Traverse the tree
        for i in range(len(self.messages)):
            print_tree_helper(self.messages[i], 0)

    def get_json(self):
        """
        Converts the conversation to a json object.

        Returns:
            dict: The json object representing the conversation.

        Example:
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "time": "2023-01-01 00:00:00",
            "messages": [
                {
                    "name": "User",
                    "role": "User",
                    "id": "12345678-1234-1234-1234-123456789012",
                    "text": "Hello, how are you?",
                    "time": "2023-01-01 00:00:00",
                    "address": "0"
                },
                {
                    "name": "Assistant",
                    "role": "Assistant",
                    "text": "I'm doing well, thank you!",
                    "time": "2023-01-01 00:00:00",
                    "address": "01"
                }
            ]
        }
        """
        if not self.messages:
            print("No messages in the conversation")
            return {}
        
        data_json = {}
        data_json["id"] = self.conv_id
        data_json["time"] = str(self.time)
        data_json["messages"] = []
        data_json["title"] = self.title

        # Helper function to recursively traverse the conversation tree
        def get_json_helper(curr):
            data = curr.to_json()
            if curr.children:
                data["children"] = []
                for child in curr.children:
                    data["children"].append(get_json_helper(child))
                    curr = child
            return data

        # Traverse the tree
        for message in self.messages:
            data_json["messages"].append(get_json_helper(message))

        return data_json
    
    def save(self):
        """
        Saves the conversation to a json file in the memory directory
        """
        if not self.messages:
            print("No messages to save")
            return

        file_path = os.path.join(settings.MEMORY_DIR, self.conv_id + ".json")
        with open(file_path, "w") as file:
            json.dump(self.get_json(), file, indent=4)

    def load(self, json_path: str):
        """
        Loads a conversation from a json file.

        Args:
            json_path (str): The path to the json file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not json_path.endswith(".json"):
            raise FileNotFoundError("File is not json")

        json_data = {}
        with open(json_path, "r") as file:
            json_data = json.load(file)

        self.load_json(json_data)
    
    def find_conversation(self):
        """
        Check if the conversation is saved in the memory directory.
        """
        memories = os.listdir(settings.MEMORY_DIR)

        # remove .json ending
        memories = [memory[:-5] for memory in memories]

        if self.conv_id in memories:
            return True
        else:
            return False
        
    def is_empty(self):
        if (self.messages is None):
            return True
        
        return len(self.messages) == 0
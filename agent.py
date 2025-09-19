import json
import os

import settings

ROLE_PATH = settings.ROLE_PATH

class Agent:
    """
    Stores information on settings and instruct for a role.

    Attributes:
        name (str): The name of the role.
        role_settings_path (str): The path to the role settings file.
        role_instruct_path (str): The path to the role instruct file.
    """
    def __init__(self, name):
        self.name = name
        self.role_settings_path = os.path.join(ROLE_PATH, self.name, self.name + ".json")
        self.role_instruct_path = os.path.join(ROLE_PATH, self.name, self.name + "_instruct.txt")

    def get_role_settings(self) -> dict:
        """
        Loads the role settings from a json file.

        Returns:
            dict: The role settings.
        """
        settings = {}
        with open(self.role_settings_path, "r") as file:
            settings = json.load(file)
        return settings
    
    def get_role_instruct(self) -> str:
        """
        Loads the role instruct from a text file.

        Returns:
            str: The role instruction.
        """
        instruct = ""
        with open(self.role_instruct_path, "r") as file:
           instruct = file.read()
        return instruct
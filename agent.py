import json
import os

import settings

AGENT_DIR = settings.AGENT_DIR

class Agent:
    """
    Stores information on settings and instruct for a agent.

    Attributes:
        name (str): The name of the agent.
        agent_settings_path (str): The path to the agent settings file.
        agent_instruct_path (str): The path to the agent instruct file.
    """
    def __init__(self, name):
        self.name = name
        # self.agent_settings_path = os.path.join(AGENT_PATH, self.name, self.name + ".json")
        # self.agent_instruct_path = os.path.join(AGENT_PATH, self.name, self.name + "_instruct.txt")

    # def get_agent_settings(self) -> dict:
    #     """
    #     Loads the agent settings from a json file.

    #     Returns:
    #         dict: The agent settings.
    #     """
    #     settings = {}
    #     with open(self.agent_settings_path, "r") as file:
    #         settings = json.load(file)
    #     return settings
    
    # def get_agent_instruct(self) -> str:
        # """
        # Loads the agent instruct from a text file.

        # Returns:
        #     str: The agent instruction.
        # """
        # instruct = ""
        # with open(self.agent_instruct_path, "r") as file:
        #    instruct = file.read()
        # return instruct
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
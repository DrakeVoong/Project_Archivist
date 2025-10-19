import json
import os
from uuid import uuid4

import settings
from nodes.node_handler import node

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
        self.agent_id = str(uuid4())
    
    def new_agent(self, new_name:str):
        self.name = new_name
        new_agent_dir_path = os.path.join(settings.AGENT_DIR, new_name)
        os.mkdir(new_agent_dir_path)

        with open(os.path.join(new_agent_dir_path, "workflow.json"), "w") as f:
            pass

    def get_workflow_list(self):
        workflows = os.listdir(settings.AGENT_DIR)
        available_agent = []
        for workflow in workflows:
            if not os.path.exists(os.path.join(settings.AGENT_DIR, workflow, "workflow.json")):
                continue
            available_agent.append(workflow)

import json
import os
from uuid import uuid4

import archivist.configs.settings as settings
from archivist.nodes.node_handler import node

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
        self.agent_id = str(uuid4())
        new_agent_dir_path = os.path.join(settings.AGENT_DIR, new_name)
        os.mkdir(new_agent_dir_path)

        with open(os.path.join(new_agent_dir_path, "workflow.json"), "w") as f:
            pass

        with open(os.path.join(new_agent_dir_path, "setting.json"), "w") as f:
            json.dump({"id":self.agent_id}, f, indent=4)

    def get_workflow_list(self):
        workflows = os.listdir(settings.AGENT_DIR)
        available_agent = []
        for workflow in workflows:
            if not os.path.exists(os.path.join(settings.AGENT_DIR, workflow, "workflow.json")):
                continue
            available_agent.append(workflow)

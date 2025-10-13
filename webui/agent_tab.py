from flask import Blueprint, request, Response
import json
import os
import copy

import settings
from nodes.node_handler import NODE_REGISTRY, import_nodes

agent_bp = Blueprint("agent", __name__)

@agent_bp.route("/get_agent_list", methods=["GET"])
def get_agent_list():
    agent_dir_list = os.listdir(settings.AGENT_DIR)

    avaliable_agents = []
    for agent in agent_dir_list:
        json_path = os.path.join(settings.AGENT_DIR, agent, "workflow.json")

        if (not os.path.exists(json_path)):
            continue

        with open(json_path, "r") as file:
            content = file.read().strip()
            if content == "":
                continue

        avaliable_agents.append(agent)

    return Response(json.dumps(avaliable_agents), mimetype="application/json")

@agent_bp.route("/save_workflow", methods=["POST"])
def save_workflow():
    data = request.json

    with open(os.path.join(settings.AGENT_DIR, "test.json"), "w") as file:
        json.dump(data, file, indent=4)

    return Response(json.dumps({"status": 200}))


@agent_bp.route("/load_agent_workflow/<agentName>", methods=["GET"])
def load_workflow(agentName):
    workflow_path = os.path.join(settings.AGENT_DIR, agentName, "workflow.json")

    with open(workflow_path, "r") as file:
        workflow = json.load(file)

    return Response(json.dumps(workflow), mimetype="application/json")

@agent_bp.route("/run_agent_workflow/<agentName>", methods=["GET"])
def run_workflow(agentName):
    pass

IMPORT_NODES = False

# Import custom python nodes
def load_nodes():
    global IMPORT_NODES
    if (not IMPORT_NODES):
        import_nodes()
        IMPORT_NODES = True

@agent_bp.route("/get_node_list", methods=["GET"])
def get_node_list():
    load_nodes()

    # Remove data not needed in frontend side
    nodes = copy.deepcopy(NODE_REGISTRY)
    for index, (node_name, node_data) in enumerate(nodes.items()):
        del node_data["callable"]

    return Response(json.dumps(nodes), mimetype="application/json")


if __name__ == "__main__":
    get_agent_list()
from flask import Blueprint, request, Response, jsonify
import json
import os
import copy

import settings
from nodes.node_handler import NODE_REGISTRY, import_nodes
from webui.workflow_manager import Workflow, running_workflow
from webui.agent import Agent

agent_bp = Blueprint("agent", __name__)

# temporary for now
agent = Agent("Archivist")

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
            # if content == "":
            #     continue

        avaliable_agents.append(agent)

    return Response(json.dumps(avaliable_agents), mimetype="application/json")

@agent_bp.route("/save_workflow", methods=["POST"])
def save_workflow():
    data = request.json
    workflow = data["workflow"]
    name = data["name"]

    with open(os.path.join(settings.AGENT_DIR, name, "workflow.json"), "w") as file:
        json.dump(workflow, file, indent=4)

    return Response(json.dumps({"status": 200}))


@agent_bp.route("/load_agent_workflow/<agentName>", methods=["GET"])
def load_workflow(agentName):
    workflow_path = os.path.join(settings.AGENT_DIR, agentName, "workflow.json")
    setting_path = os.path.join(settings.AGENT_DIR, agentName, "setting.json")

    data = {"workflow": "", "setting": ""}
    with open(setting_path, "r") as file:
        setting = json.load(file)
    data["setting"] = setting

    if os.path.getsize(workflow_path) == 0:
        return Response(json.dumps(data), mimetype="application/json")

    with open(workflow_path, "r") as file:
        workflow = json.load(file)
    data["workflow"] = workflow

    return Response(json.dumps(data), mimetype="application/json")

@agent_bp.route("/new_workflow", methods=["POST"])
def new_workflow():
    data = request.json

    agent.new_agent(data["name"])

    return Response(json.dumps({"id": agent.agent_id}), mimetype="application/json")

@agent_bp.route("/run_agent_workflow", methods=["POST"])
def run_workflow():
    workflow_data = request.json

    workflow = Workflow()
    workflow.load_workflow(workflow_data)
    workflow.convert_to_nodes()
    workflow.get_node_tree()
    workflow.map_node_to_func(NODE_REGISTRY)
    workflow.call_funcs(NODE_REGISTRY)

    json_data = [[node.to_json() for node in level] for level in workflow.node_tree]

    return Response(json.dumps(json_data), mimetype="application/json")

@agent_bp.route("/add_workflow_to_events", methods=["POST"])
def add_workflow():
    data = request.json
    agentName = data["name"]
    
    workflow = Workflow()
    workflow.load_workflow_file(agentName)
    workflow.convert_to_nodes()
    workflow.map_node_to_func(NODE_REGISTRY)

    # found_on_message = False
    running_workflow.append(workflow.func_tree)
    # for level in workflow.func_tree:
    #     for func in level:
    #         if func.type == "trigger_events.on_message.on_meesage":
    #             found_on_message = True
    #             break
    #     if found_on_message:
    #         break

    return Response(json.dumps({"status": 200}))
    

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
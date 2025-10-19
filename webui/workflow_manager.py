from dataclasses import dataclass, field
from typing import Optional, List, Callable, Any
import json
import os

import settings

running_workflow = []

@dataclass
class Node:
    id: int
    type: str
    needs: list
    settings: list
    dependants: list

    def __str__(self):
        return (f"id - {self.id}, type - {self.type}, needs - {self.needs}, settings - {self.settings}, dependants - {self.dependants}")
    
    def to_json(self):
        data = {}
        data["id"] = self.id
        data["type"] = self.type
        data["needs"] = self.needs
        data["settings"] = self.settings
        data["dependants"] = self.dependants
        return data
    
@dataclass
class Func:
    id: int
    callable: Callable[..., Any]
    inputs: list
    settings: list
    outputs: list

    def __str__(self):
        return (f"id - {self.id}, callable - {self.callable}, inputs - {self.inputs}, settings - {self.settings}, outputs - {self.outputs}")

class Workflow:
    def __init__(self):
        self.node_tree = []

    def load_workflow(self, json_data):
        self.workflow_JSON = json_data

    def load_workflow_file(self, name):
        with open(os.path.join(settings.AGENT_DIR, name, "test.json"), "r") as file:
            self.workflow_JSON = json.load(file)

    def convert_to_nodes(self):
        """
        Convert the workflow json exported by Drawflow into a list of nodes.
        """
        data = self.workflow_JSON["drawflow"]["Home"]["data"]
        nodes = []
        for index, (data_key, data_value) in enumerate(data.items()):
            # Find needs
            node_id = data_value["id"]
            needs = []
            inputs = data_value["inputs"]
            for input_index, (input_key, input_value) in enumerate(inputs.items()):
                # Add error check if more than one connections are in an input
                if len(input_value["connections"]) == 0:
                    continue

                for connection in input_value["connections"]:
                    needs.append(connection)

                # needs.add(input_value["connections"][0]["node"])

            # Find settings
            settings = []
            node_data = data_value["data"]
            for node_data_index, (node_data_key, node_data_value) in enumerate(node_data.items()):
                if node_data_key.startswith(f"setting_"):
                    node_data_num = node_data_key.split("_")[1]
                    settings.append({node_data_num: node_data_value})

            # Find dependants
            dependants = []
            outputs = data_value["outputs"]
            for outputs_index, (output_key, output_value) in enumerate(outputs.items()):
                if len(output_value["connections"]) == 0:
                    continue

                for connection in output_value["connections"]:
                    dependants.append(connection)

                # dependants.add(output_value["connections"][0]["node"])


            node = Node(data_key, data_value["name"], needs, dependants)
            nodes.append(node)
        self.nodes = nodes

    def get_node_tree(self):
        """
        Calculate the depth of nodes from start (depth=0) nodes to end (depth=nth) nodes.
        \nNodes with no inputs (i.e. no nodes feeding into it) are closer to start.
        \nNodes that require other nodes to be processed first are higher in depth.
        """
        old_seen = set()
        new_seen = set()
        for i in range(len(self.nodes)):
            self.node_tree.append([])
            for index, node in enumerate(self.nodes):
                if (str(node.id) in new_seen):
                    continue

                set_needs = set([node["node"] for node in node.needs])

                if (not set_needs.issubset(old_seen) and set_needs != old_seen):
                    continue

                self.node_tree[i].append(node)
                new_seen.add(str(node.id))
            old_seen = new_seen

        self.node_tree = [level for level in self.node_tree if level != []]

    def map_node_to_func(self, NODE_REGISTRY: dict):
        self.func_tree = []
        for i in range(len(self.node_tree)):
            self.func_tree.append([])
            for node in self.node_tree[i]:
                if node.type not in NODE_REGISTRY:
                    print("Node type not available")
                    raise ValueError("node type not available")

                # Check if all input in node has been filled
                if len(node.needs) != len(NODE_REGISTRY[node.type]["inputs"]):
                    print("Not all input has been filled.")
                    raise ValueError("Not all input has been filled.")
                
                function_outputs = node.dependants
                for index in range(len(function_outputs)):
                    function_outputs[index]["output"] = int(function_outputs[index]["output"].split("_")[1])

                function_input = node.needs
                for index in range(len(function_input)):
                    function_input[index]["input"] = int(function_input[index]["input"].split("_")[1])

                
                function = Func(node.id, NODE_REGISTRY[node.type]["callable"], node.needs, node.settings, node.dependants)
                self.func_tree[i].append(function)

        print(self.func_tree)

    def call_funcs(self, NODE_REGISTRY: dict):
        variables = {}
        for i in range(len(self.func_tree)):
            for func in self.func_tree[i]:
                if len(func.inputs + func.settings) == 0:
                    if len(func.outputs) == 0:
                        func.callable()
                    else:
                        result = func.callable()
                else:

                    args = []

                    for input in func.inputs:
                        args.append(variables[input["node"]][input["input"]-1])

                    for index, setting in enumerate(func.settings):
                        args.append(setting[str(index+1)])

                    if len(func.outputs) == 0:
                        func.callable(*args)
                    else:
                        result = func.callable(*args)
                
                variables[func.id] = []
                variables[func.id].append(result)

    def run_node_tree(self):
        pass
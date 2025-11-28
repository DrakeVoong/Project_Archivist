from dataclasses import dataclass, field
from typing import Optional, List, Callable, Any, Generator
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
    type: str
    inputs: list
    settings: list
    outputs: list
    trigger_inputs: dict
    send_outputs: dict


    def __str__(self):
        return (f"id - {self.id}, callable - {self.callable}, inputs - {self.inputs}, settings - {self.settings}, outputs - {self.outputs}, trigger inputs - {self.trigger_inputs}")

class Workflow:
    def __init__(self):
        self.node_tree = []

    def load_workflow(self, json_data):
        self.workflow_JSON = json_data

    def load_workflow_file(self, name):
        with open(os.path.join(settings.AGENT_DIR, name, "workflow.json"), "r") as file:
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
                # TODO: Add error check if more than one connections are in an input
                if len(input_value["connections"]) == 0:
                    continue
                for connection in input_value["connections"]:
                    needs.append(connection)

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

            node = Node(data_key, data_value["name"], needs, settings, dependants)
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
                    raise ValueError(f"Node type: {node.type} not in node registry")

                #Check if all input in node has been filled
                if len(node.needs) != len(NODE_REGISTRY[node.type]["inputs"]):
                    raise ValueError("Not all input has been filled.")
                

                # Dict of which function requires values as arguments from this function's return(s)
                # Convert into {"node": id, input: port} format
                for index in range(len(node.dependants)):
                    node.dependants[index]["output"] = int(node.dependants[index]["output"].split("_")[1])

                # TODO: Should probably be changed to deep copy of the nodes values
                
                # Dict of which which function this node needs as arguments
                # Convert into {"N"}
                for index in range(len(node.needs)):
                    node.needs[index]["input"] = int(node.needs[index]["input"].split("_")[1])

                node_data = NODE_REGISTRY[node.type]
                function_trigger_inputs = node_data["trigger_inputs"]
                function_send_outputs = node_data["send_outputs"]
                
                function = Func(node.id, NODE_REGISTRY[node.type]["callable"], node.type, node.needs, node.settings, node.dependants, function_trigger_inputs, function_send_outputs)
                self.func_tree[i].append(function)

    def call_funcs(self, func_tree, trigger_inputs):
        """
        
        trigger_inputs: {"function name":{"arg1_name": arg1, "arg2_name": arg2, ...}}
        """
        variables = {}
        for i in range(len(func_tree)):
            print(variables)
            for func in func_tree[i]:
                func_trigger_inputs = [arg_name for index, (arg_name, arg) in enumerate(func.trigger_inputs.items())]

                if len(func.inputs + func.settings + func_trigger_inputs) == 0:
                    if len(func.outputs) == 0:
                        func.callable()
                    else:
                        result = func.callable()
                else:

                    args = []

                    # Check for any trigger events variables
                    for index, (arg_name, arg_type) in enumerate(func.trigger_inputs.items()):
                        recieved_arg_type = type(trigger_inputs[func.type][arg_name]).__name__
                        if recieved_arg_type != arg_type:
                            raise TypeError(f"Invalid type for function argument. Function: {func.type} with arg: {arg_name}, type: {arg_type}, instead got type: {recieved_arg_type}")
                        
                        args.append(trigger_inputs[func.type][arg_name])

                    for input in func.inputs:
                        args.append(variables[input["node"]][input["input"]-1])

                    for index, setting in enumerate(func.settings):
                        args.append(setting[str(index+1)])

                    if len(func.outputs) + len(func.send_outputs) == 0:
                        func.callable(*args)
                    else:
                        result = func.callable(*args)

                # Assuming that generator from send_message is the last node to be processed
                # probably should fix it but idk how
                total_index = len(func.outputs) + len(func.send_outputs)
                if type(result) == tuple:
                    result = list(result)
                    for i in range(len(result)):
                        if type(result[i]) == Generator and ((i+1) >= total_index):
                            return result[i]
                else:
                    if hasattr(type(result), "__name__"):
                        if type(result).__name__ == "generator" and ((i+1) >= total_index):
                            return result
                
                # Store return values to retrieve them for later nodes
                # unpack return values from functions
                variables[func.id] = []
                if type(result) == tuple or type(result) == list:
                    result = list(result)
                    variables[func.id] = result
                else:
                    variables[func.id].append(result)

        return {"status": "success"}

    def run_node_tree(self):
        pass
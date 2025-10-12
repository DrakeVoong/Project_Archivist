from dataclasses import dataclass, field
from typing import Optional, List
import json
import os

import settings

@dataclass
class Node:
    id: int
    type: str
    needs: set
    dependants: set

    def __str__(self):
        return (f"id - {self.id}, type - {self.type}, needs - {self.needs}, dependants - {self.dependants}")


class Workflow:
    def __init__(self):
        self.node_tree = []

    def load_workflow_JSON(self, name):
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
            needs = set()
            inputs = data_value["inputs"]
            for input_index, (input_key, input_value) in enumerate(inputs.items()):
                # Add error check if more than one connections are in an input
                if len(input_value["connections"]) == 0:
                    continue

                needs.add(input_value["connections"][0]["node"])

            # Find dependants
            dependants = set()
            outputs = data_value["outputs"]
            for outputs_index, (output_key, output_value) in enumerate(outputs.items()):
                if len(output_value["connections"]) == 0:
                    continue

                dependants.add(output_value["connections"][0]["node"])

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

                if (not node.needs.issubset(old_seen) and node.needs != old_seen):
                    continue

                self.node_tree[i].append(node)
                new_seen.add(str(node.id))
            old_seen = new_seen

        self.node_tree = [level for level in self.node_tree if level != []]
        print(self.node_tree)
from typing import Generator
import json

from archivist.nodes.node_handler import node

@node(settings=["string"], outputs=["string"])
def string_textbox(string: str) -> tuple[str]:
    return string

@node(inputs=["string"])
def print_string(string: str):
    print(string)

@node(inputs=["stringA", "stringB"], outputs=["string"])
def concat_string(stringA: str, stringB: str) -> tuple[str]:
    return stringA + stringB

# Testing functions for generator and streaming
def segmenting_string(string):
    for i in range(len(string)):
        yield json.dumps({"type":"message", "value": string[i]}) + "\n"

@node(inputs=["string"], send_outputs=["chars"])
def segment_string(string: str) -> tuple[Generator]:
    return segmenting_string(string)
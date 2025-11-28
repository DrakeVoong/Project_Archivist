from typing import Generator

from archivist.nodes.node_handler import node

@node(inputs=["response"], send_outputs=["response"])
def send_message(response: Generator) -> tuple[Generator]:
    return response
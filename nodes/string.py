from nodes.node_handler import node

@node(inputs=["string"], settings=[], outputs=[])
def print_string(string: str):
    print(string)
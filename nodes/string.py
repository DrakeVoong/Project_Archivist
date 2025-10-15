from nodes.node_handler import node

@node(settings=["string"], outputs=["string"])
def string_textbox(string: str) -> tuple[str]:
    return string

@node(inputs=["string"])
def print_string(string: str):
    print(string)

@node(inputs=["stringA", "stringB"], outputs=["string"])
def concat_string(stringA: str, stringB: str) -> tuple[str]:
    return stringA + stringB
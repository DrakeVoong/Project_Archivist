from ..node_handler import node

@node(inputs=[], settings=[], outputs=["message", "address"])
def on_message(message:str, address:str) -> tuple[str, str]:
    """
    When a message is sent via chatbox.
    """
    return message, address

from nodes.node_handler import node

@node(inputs=[], settings=[], outputs=["message", "address", "type"], trigger_inputs=["message", "address", "msg_type"])
def on_message(message: str, address: str, msg_type: str) -> tuple[str, str, str]:
    """
    When a message is sent via chatbox.
    """

    return message, address, msg_type

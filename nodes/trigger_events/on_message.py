from flask import request

from ..node_handler import node

@node(inputs=[], settings=[], outputs=["message", "address", "type"])
def on_message() -> tuple[str, str, str]:
    """
    When a message is sent via chatbox.
    """

    data = request.json
    message = data["text"]
    address = data["address"]
    msg_type = data["msg_type"]

    return message, address, msg_type

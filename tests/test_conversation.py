import pytest

from modules.message_manager import Message_Node, Conversation, MessageAddressError


def test_message_node_creation():
    message1 = Message_Node("Adam", "User", "Hello, how are you?")    

    assert str(message1) == (f"Name - Adam, Role - User, id - {message1.id},"
                             f" text - Hello, how are you?, time - {message1.time}, address - "
                            )

def test_add_message_empty_conversation():
    empty_conv = Conversation()

    message1 = Message_Node("Message 1", "User", "Hello, how are you?")
    with pytest.raises(MessageAddressError):
        empty_conv.add_message(message1, "00")

def test_add_message_empty():
    empty_conv = Conversation()

    message1 = Message_Node("Message 1", "User", "Hello, how are you?")
    empty_conv.add_message(message1, "")

    assert str(empty_conv.get_message("0")) == str(message1)

def test_get_message_empty_conversation():
    empty_conv = Conversation()
    with pytest.raises(MessageAddressError):
        empty_conv.get_message("0")

def test_get_message_empty_string():
    conv = Conversation()

    message1 = Message_Node("Message 1", "User", "Hello, how are you?")
    conv.add_message(message1, "")
    with pytest.raises(MessageAddressError):
        conv.get_message("")

def test_get_message():
    conv = Conversation()

    message1 = Message_Node("Message 1", "User", "Hello, how are you?")
    conv.add_message(message1, "")

    assert str(conv.get_message("0")) == str(message1)


def test_delete_message():
    conv = Conversation()

    message1 = Message_Node("Message 1", "User", "Hello, how are you?")
    conv.add_message(message1, "")
    message2 = Message_Node("Message 2", "Assistant", "I'm doing well, thank you for asking!")
    conv.add_message(message2, "0")

    conv.delete_message("00")
    with pytest.raises(MessageAddressError):
        conv.get_message("00")

def test_get_conv_list_empty():
    conv = Conversation()
    assert conv.get_conv_list() == []

def test_get_conv_list():
    conv = Conversation()

    message1 = Message_Node("Message 1", "User", "Hello, how are you?")
    conv.add_message(message1, "")
    message2 = Message_Node("Message 2", "Assistant", "I'm doing well, thank you for asking!")
    conv.add_message(message2, "0")

    assert conv.get_conv_list() == [message1.to_json(), message2.to_json()]

# TODO: add test case for loading json memory
import pytest
import pytest_mock
from uuid import uuid4
import pandas as pd
import os
from datetime import datetime

from modules.message_manager import Message_Node, Conversation
from modules.vectorDB.vector import VectorDB


@pytest.fixture
def conv():
    conv = Conversation()

    message1 = Message_Node("Message 1", "User", "Hello, how are you?")
    conv.add_message(message1, "")
    message2 = Message_Node("Message 2", "Assistant", "I'm doing well, thank you for asking!")
    conv.add_message(message2, "0")

    yield conv


def test_save_conv_to_pd(conv, tmp_path):
    conv_dir = "vectors\\conv\\"
    path_1 = os.path.join(tmp_path, conv_dir)

    os.mkdir(os.path.join(tmp_path, "vectors\\"))
    os.mkdir(path_1)

    vector_manager = VectorDB(tmp_path)
    df_1 = vector_manager.save_conv_to_pd(conv)
    df_2 = pd.read_pickle(os.path.join(path_1, conv.conv_id))

    assert df_1.equals(df_2)
    
    
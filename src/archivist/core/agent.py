from pathlib import Path

from archivist.config.settings import AGENT_PATH
from archivist.LLM_providers.LLM_provider import LLMProvider
from archivist.core.conversation import Conversation
from archivist.core.message import MessageNode

# System instruction is static for now
# No agent specific hyperparameters
# TODO: implement conversation construction to pass to provider

class Agent:
    def __init__(self, provider:LLMProvider, name:str, conversation:Conversation) -> None:
        self.provider = provider
        self.name = name
        self._get_agent_sys_instruct()

    def _get_agent_sys_instruct(self):
        sys_instruct_path = Path(AGENT_PATH / f"{self.name}.md")
        if not sys_instruct_path.exists():
            raise FileNotFoundError(f'File {sys_instruct_path} not found.') 

        self.system_instruct = sys_instruct_path.read_text()

    def generate_response(self, message_node:MessageNode):
        self.provider.generate(message_node.message.content.text)
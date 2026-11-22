from pathlib import Path

from archivist.config.settings import AGENT_PATH
from archivist.LLM_providers.LLM_provider import LLMProvider
from archivist.core.conversation import Conversation
from archivist.core.message import MessageNode

# System instruction is static for now
# No agent specific hyperparameters
# TODO: implement conversation construction to pass to provider

class Agent:
    def __init__(self, name:str) -> None:
        self.name = name
        self.AGENT_DIR = Path(AGENT_PATH / name)
        self._load_sys_instruct()

    def _load_sys_instruct(self):
        sys_instruct_path = Path(self.AGENT_DIR / f"{self.name}.md")
        if not sys_instruct_path.exists():
            raise FileNotFoundError(f'File {sys_instruct_path} not found.') 

        self.system_instruct = sys_instruct_path.read_text()
import json
import logging

log = logging.getLogger(__name__)

from archivist.core.type import SamplingConfig
from archivist.config.settings import AGENT_PATH

# System instruction is static for now
# No agent specific hyperparameters
# TODO: implement conversation construction to pass to provider

class Agent:
    def __init__(self, name:str) -> None:
        self.name = name
        self.AGENT_DIR = AGENT_PATH / name
        self.system_instruct = self._get_sys_instruct()
        self.sampling = self._get_sampling()
        log.info("Loaded agent %s", self.name)

    def _get_sys_instruct(self):
        sys_instruct_path = self.AGENT_DIR / f"{self.name}.md"
        if not sys_instruct_path.exists():
            raise FileNotFoundError(f'File {sys_instruct_path} not found.') 

        return sys_instruct_path.read_text()

    def _get_sampling(self) -> SamplingConfig:
        sampling_path = self.AGENT_DIR / "config.json"
        if not sampling_path.exists():
                    raise FileNotFoundError(f'File {sampling_path} not found.') 

        with open(sampling_path) as f:
            return SamplingConfig(**json.load(f))
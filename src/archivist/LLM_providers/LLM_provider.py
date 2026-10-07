from abc import ABC, abstractmethod
from typing import Generator


class LLMProvider(ABC):
    @abstractmethod
    def connect(self, config: list) -> int:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def generate(self, messages) -> dict:
        pass

    @abstractmethod
    def generate_stream(self, messages) -> Generator:
        pass

    @abstractmethod
    def get_status(self) -> int:
        pass
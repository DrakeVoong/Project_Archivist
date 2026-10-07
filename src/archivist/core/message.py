from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import uuid

from archivist.LLM_providers.LLM_provider import LLMProvider


@dataclass
class contentType:
    text: str
    image: Optional[str] = None

@dataclass
class Message:
    name: str
    content: str
    id: uuid.UUID = field(init=False, default_factory=uuid.uuid4)
    _time: float = field(init=False, default_factory=lambda: datetime.now().timestamp())

    @property
    def time(self):
        return int(self._time * 1000)

@dataclass
class MessageNode:
    message: Message
    parent: MessageNode | None = None
    children: list[MessageNode] = field(default_factory=list)

@dataclass
class SystemMessage(Message):
    pass

@dataclass
class UserMessage(Message):
    attachments: list[str] = field(default_factory=list)

@dataclass
class AssistantMessage(Message):
    model: str
    provider: LLMProvider
    finish_reason: str = ""

@dataclass 
class ToolMessage(Message):
    success: bool = False
    retry: int = 0

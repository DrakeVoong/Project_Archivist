from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, ClassVar
from datetime import datetime
import time
import uuid

from archivist.LLM_providers.LLM_provider import LLMProvider


@dataclass
class ContentType:
    text: str
    image: Optional[str] = None

@dataclass
class Message:
    role: ClassVar[str]
    name: str
    content: ContentType
    id: uuid.UUID = field(init=False, default_factory=uuid.uuid4)
    time_ns: float = field(init=False, default_factory=time.time_ns)

@dataclass
class MessageNode:
    message: Message
    parent: MessageNode | None = None
    children: list[MessageNode] = field(default_factory=list)

    @property
    def parent_id(self):
        return self.parent.message.id if self.parent else None

@dataclass
class SystemMessage(Message):
    role: ClassVar[str] = "system"

@dataclass
class UserMessage(Message):
    role: ClassVar[str] = "user"

@dataclass
class AssistantMessage(Message):
    role: ClassVar[str] = "assistant"
    model: str = ""
    finish_reason: str = ""

@dataclass 
class ToolMessage(Message):
    role: ClassVar[str] = "tool"
    success: bool = False
    retry: int = 0

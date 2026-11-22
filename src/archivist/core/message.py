from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, ClassVar
import time
import uuid


@dataclass
class Content:
    text: str
    image: Optional[str] = None

@dataclass(frozen=True)
class Message:
    role: ClassVar[str]
    name: str
    content: Content
    id: uuid.UUID = field(init=False, default_factory=uuid.uuid4)
    time_ns: int = field(init=False, default_factory=time.time_ns)

@dataclass
class MessageNode:
    message: Message
    parent: MessageNode | None = None
    children: list[MessageNode] = field(default_factory=list)

    @property
    def parent_id(self):
        return self.parent.message.id if self.parent else None

@dataclass(frozen=True)
class SystemMessage(Message):
    role: ClassVar[str] = "system"

@dataclass(frozen=True)
class UserMessage(Message):
    role: ClassVar[str] = "user"

@dataclass(frozen=True)
class AssistantMessage(Message):
    role: ClassVar[str] = "assistant"
    model: str = ""
    finish_reason: str = ""

@dataclass(frozen=True)
class ToolMessage(Message):
    role: ClassVar[str] = "tool"
    success: bool = False
    retry: int = 0

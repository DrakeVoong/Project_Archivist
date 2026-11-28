from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, ClassVar, Any
import time
import uuid

# ---------- Message ----------
@dataclass
class Content:
    text: str
    image: Optional[str] = None

@dataclass(frozen=True)
class Message:
    role: ClassVar[str]
    name: str
    content: Content
    id: uuid.UUID = field(default_factory=uuid.uuid4, kw_only=True)
    time_ns: int = field(default_factory=time.time_ns, kw_only=True)

def message_from_row(row:dict) -> Message:
    text = (row["content"][0]["text"] or "") if row["content"] else ""
    common:dict[str, Any] = dict(
        name=row["name"] or "",
        content=Content(text),
        id=uuid.UUID(row["uuid"]),
        time_ns=row["time_ns"],
    )
    role = row["role"]
    if role == "assistant":
        return AssistantMessage(
            **common,
            reasoning=row["reasoning"],
            model=row["model"],
            finish_reason=row["finish_reason"] or "",
            tool_calls=tuple(ToolCall(**tc) for tc in row["tool_calls"]),
        )
    if role == "tool":
        return ToolMessage(**common, tool_call_id=row["tool_call_id"],
                           success=row["success"], retry=row["retry"] or 0)
    if role == "user":
        return UserMessage(**common)
    return SystemMessage(**common)


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
    reasoning: str | None = None
    model: str = ""
    finish_reason: str = ""
    tool_calls: tuple[ToolCall, ...] = ()

@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str

@dataclass(frozen=True)
class ToolMessage(Message):
    role: ClassVar[str] = "tool"
    tool_call_id: str
    success: bool = False
    retry: int = 0


# ---------- Configs ----------

@dataclass()
class SamplingConfig:
    temperature: int
    top_p: int
    top_k: int
    min_p: int
    presence_penalty: int
    repetition_penalty: int

    def get_openai_llamacpp_kwargs(self) -> dict:
        return {"top_k":self.top_k,
                "min_p":self.min_p,
                "repetition_penalty":self.repetition_penalty}
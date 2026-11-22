from archivist.core.message import Message, UserMessage, AssistantMessage, ToolMessage, SystemMessage

# TODO: support for different content types.
def convert_to_openai(message: Message) -> dict[str, str]:
    match message:
        case SystemMessage():
            return {"role":"system", "content":message.content.text}
        case UserMessage():
            return {"role":"user", "content":message.content.text}
        case AssistantMessage():
            return {"role":"assistant", "content":message.content.text}
        case ToolMessage():
            raise NotImplementedError("ToolMessage serialization not yet implemented")
        case _:
            raise TypeError("Not a valid Message class")
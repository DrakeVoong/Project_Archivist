from archivist.core.message import Message, UserMessage, AssistantMessage, ToolMessage, SystemMessage
from openai.types.chat import ChatCompletionMessageParam

# TODO: support for different content types.
def convert_to_openai(message: Message) -> ChatCompletionMessageParam:
    match message:
        case SystemMessage():
            return {"role":"system", "content":message.content.text}
        case UserMessage():
            return {"role":"user", "content":message.content.text}
        case AssistantMessage():
            openai_message = {"role":"assistant", "content":message.content.text}
            if message.reasoning:
                openai_message["reasoning_content"] = message.reasoning
            if message.tool_calls:
                openai_message["tool_calls"] = message.tool_calls
            return openai_message
        case ToolMessage():
            return {"role":"tool", "tool_call_id":message.tool_call_id, "content":message.content.text}
        case _:
            raise TypeError("Not a valid Message class")
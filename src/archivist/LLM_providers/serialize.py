from archivist.core.type import Message, UserMessage, AssistantMessage, ToolMessage, SystemMessage
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionAssistantMessageParam 

# TODO: support for different content .
def convert_to_openai(message: Message) -> ChatCompletionMessageParam:
    match message:
        case SystemMessage():
            return {"role":"system", "content":message.content.text}
        case UserMessage():
            return {"role":"user", "content":message.content.text}
        case AssistantMessage():
            openai_message:ChatCompletionAssistantMessageParam  = {"role":"assistant", "content":message.content.text}
            if message.reasoning:
                openai_message["reasoning_content"] = message.reasoning # type: ignore[typeddict-unknown-key]
            if message.tool_calls:
                openai_message["tool_calls"] = [
                    {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                    }
                    for tc in message.tool_calls
                ]
            return openai_message
        case ToolMessage():
            return {"role":"tool", "tool_call_id":message.tool_call_id, "content":message.content.text}
        case _:
            raise TypeError("Not a valid Message class")
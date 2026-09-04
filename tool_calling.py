from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url="https://openrouter.ai/api/v1"
)


# now we are going to implement tool calling in Ai Agents


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# print(read_file("notes.txt")) # for debugging purpose

# now we are going to define the Tool Schema

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Reads a text file and returns its content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the text file to read.",
                }
            },
            "required": ["path"],
        },
    },
}

messages = [
    {
        "role": "user",
        "content": "What is inside notes.txt summarise it in one line precisely.",
    }
]

while True:
    response = client.chat.completions.create(
        model="minimax/minimax-m3:free",
        messages=messages,
        tools=[TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "read_file"}},
    )
    message = response.choices[0].message
    print(message)
    messages.append(message)

    # no tool calls means the model is done and gave us a normal answeer

    if not message.tool_calls:
        print(message.content)
        break
    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)

        print(f"Model wants to run: read_file({args})")

        result = read_file(**args)

        messages.append(
            {"role": "tool", "tool_call_id": tool_call.id, "content": result}
        )

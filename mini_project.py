from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()
import subprocess

SYSTEM_PROMPT = """
You're a coding agent running in the user's terminal.
You can list files, read files, write files and run shell commands.
Use your tools to complete the user's task, then briefly summarize what you did.
The working directory is the folder the user launched you from.
"""


# tool definitions


def list_files(path="."):
    entries = []
    for entry in os.scandir(path):
        entries.append(entry.name + ("/" if entry.is_dir() else ""))
    return "\n".join(sorted(entries)) or "(empty directory)"


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url="https://openrouter.ai/api/v1"
)


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Content Saved in {path} with {len(content)} characters"


def run_commands(command):
    user_answer = input(f"Running {command} ? [y/n]: ")
    if user_answer.strip().lower() != "y":  # user denied the permission
        return f"The user declined to run this command."
    else:  # will run the command
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=120
        )
        output = (result.stdout + result.stderr).strip()
        return output or f"No output ,exit code {result.returncode}"


TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_commands": run_commands,
    "list_files": list_files,
}

# now we will write schemas of these tools

# ===============================TOOLS SCHEMAS==================================
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files and directories inside the specified directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to list. Defaults to the current directory.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to read.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates the file if it does not exist or overwrites existing content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write into the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_commands",
            "description": "Execute a shell command after asking the user for permission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute.",
                    }
                },
                "required": ["command"],
            },
        },
    },
]
# ===============================TOOLS SCHEMAS==================================


def run_tool(tool_call):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    print(f"Tool: {name} ({args})")
    try:
        return str(TOOLS[name](**args))
    except Exception as error:
        return f"Error {error}"


def run_agent(messages):
    while True:
        response = client.chat.completions.create(
            model="minimax/minimax-m3:free", messages=messages, tools=tools_schema
        )

        message = response.choices[0].message
        messages.append(message)

        # no tool call mean that the model has answered in plain text and no tools are used
        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            result = run_tool(tool_call)
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": result}
            )


def main():
    messages = [{"role": "system","content":SYSTEM_PROMPT}]
    print("Mini agent ready. Type exit to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit","quit"):
            break
        messages.append({"role":  "user","content": user_input})
        reply = run_agent(messages)
        print(f"\nAgent: {reply}")


if __name__ == "__main__":
    main()

# 🤖 AI Agent with Tool Calling

<p align="center">
  <strong>A Python-based AI coding agent that uses LLM tool calling to interact with a local development environment.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/LLM-Tool%20Calling-purple" alt="LLM Tool Calling">
  <img src="https://img.shields.io/badge/OpenRouter-API-orange" alt="OpenRouter">
  <img src="https://img.shields.io/badge/OpenAI-SDK-green" alt="OpenAI SDK">
  <img src="https://img.shields.io/badge/uv-Package%20Manager-blueviolet" alt="uv">
</p>

---

## 📌 Overview

This project is a **Python AI coding agent** built to understand the fundamental architecture behind **LLM-powered agents and tool calling**.

Instead of only generating text, the agent can interact with the local development environment through custom tools.

It can:

* 📂 Inspect files and directories
* 📖 Read source code
* ✍️ Create and modify files
* 💻 Execute terminal commands
* 🔄 Receive tool results and continue working
* 🧑‍💻 Ask for human approval before executing shell commands

The project demonstrates a simple but important agentic pattern:

> **LLM → Tool Call → Python Function → Environment → Tool Result → LLM → Next Action**

---

## 🎮 Demo: The Agent Built a Snake Game

To test the agent beyond simple conversations, I gave it a practical software-development task:

```text
Create a Snake game from scratch.
```

The agent used its available tools to inspect the workspace, create files, run the game, inspect the generated code, and iteratively improve it.

The result is a feature-rich **Snake Game — Enhanced Edition v2**.

### 🐍 Snake Game

The generated game includes:

* 🎮 Arrow-key and WASD controls
* 👥 Two-player mode
* 🗺️ Six obstacle maps
* ⚡ Power-ups
* 💥 Particle effects
* 🔊 Procedurally generated sound effects
* 🌈 Four color schemes
* 🌀 Wrap-around mode
* 📈 Increasing difficulty
* 🏆 Persistent high scores
* 📊 Pause-screen statistics
* 💾 Persistent game settings

### 📁 Game Files

The Snake game lives inside the [`snake_game/`](snake_game/) directory:

```text
snake_game/
├── snake_game.py
├── prompt.txt
├── prompt_v2.md
├── README.md
├── highscore.txt
└── settings.txt
```

### ▶️ Run the Game

```bash
cd snake_game
python snake_game.py
```

Install Pygame first if necessary:

```bash
pip install pygame
```

Or, for Python versions where the standard package causes installation issues:

```bash
pip install pygame-ce
```

### 🎯 Example Agent Workflow

```text
User:
"Create a Snake game from scratch"

        ↓

      LLM
        ↓
  Decide next action
        ↓
    Tool Call
        ↓
   Python Tool
        ↓
┌───────────────────┐
│ list_files()      │
│ read_file()       │
│ write_file()      │
│ run_commands()    │
└───────────────────┘
        ↓
  Tool Result
        ↓
      LLM
        ↓
 Inspect / Modify / Run
        ↓
      Repeat
```

This allowed me to see how an LLM can move from **generating code** to actually participating in an iterative software-development workflow.

---

## 🧠 How Tool Calling Works

The LLM does **not directly execute Python functions or terminal commands**.

Instead, the application provides the model with descriptions of available tools using **JSON schemas**.

For example, the model is told that a tool called `read_file` exists and that it requires a `path` parameter.

The process is:

```text
1. User gives the agent a task
          ↓
2. LLM analyzes the task
          ↓
3. LLM requests a tool
          ↓
4. Python receives the tool call
          ↓
5. Python executes the corresponding function
          ↓
6. Tool result is returned to the LLM
          ↓
7. LLM decides what to do next
          ↓
8. Repeat until the task is complete
```

The important distinction is:

```text
LLM
 ↓
Requests an action

Python
 ↓
Actually performs the action
```

This separation is the foundation of the tool-using agent architecture implemented in this project.

---

## 🛠️ Available Tools

| Tool           | Description                                        |
| -------------- | -------------------------------------------------- |
| `list_files`   | Lists files and directories in a specified path    |
| `read_file`    | Reads the contents of a text file                  |
| `write_file`   | Creates or overwrites a file with provided content |
| `run_commands` | Executes a shell command after user approval       |

### `list_files`

Allows the agent to inspect the development environment.

```python
list_files(path=".")
```

### `read_file`

Allows the agent to inspect source code and other text files.

```python
read_file(path="snake_game/snake_game.py")
```

### `write_file`

Allows the agent to create or modify files.

```python
write_file(
    path="example.py",
    content="print('Hello World')"
)
```

### `run_commands`

Allows the agent to execute terminal commands, but only after explicit human approval.

```text
Running python snake_game.py ? [y/n]:
```

---

## 🔄 The Agent Loop

The core agent loop continuously checks whether the LLM wants to use a tool.

Conceptually:

```text
while task_not_finished:

    send messages + available tools to LLM

    if LLM requests a tool:

        extract tool name
        extract arguments

        execute Python function

        send result back to LLM

    else:

        return final response
```

In this implementation, `run_agent()` handles this loop.

The model can therefore perform multiple actions during a single user request rather than stopping after generating one response.

---

## 🔐 Human-in-the-Loop Guardrail

Shell commands require explicit user approval.

```text
Running <command> ? [y/n]:
```

The command executes only when the user confirms with:

```text
y
```

This provides a basic **human-in-the-loop safety mechanism**.

However, this is intentionally a learning project rather than a production-secure coding agent.

Potential future security controls include:

* Command allowlists
* Restricted working directories
* File-system sandboxing
* Process isolation
* Permission levels
* Resource limits
* Stronger validation of tool arguments

---

## 🏗️ Architecture

```text
                    ┌──────────────┐
                    │     User     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     LLM      │
                    └──────┬───────┘
                           │
                    Tool Call Request
                           │
                           ▼
                    ┌──────────────┐
                    │  run_tool()  │
                    └──────┬───────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       list_files()   read_file()   write_file()
                           │
                           │
                           ▼
                    run_commands()
                           │
                           ▼
                 Local Environment
                           │
                           ▼
                     Tool Result
                           │
                           ▼
                    ┌──────────────┐
                    │     LLM      │
                    └──────┬───────┘
                           │
                           ▼
                 Next Action / Answer
```

---

## 📂 Project Structure

```text
agent-tool-calling/
│
├── agent.py                 # Main AI coding agent
│
├── snake_game/              # Game created and iteratively improved
│   ├── snake_game.py        # Main Snake game
│   ├── prompt.txt           # Original development specification
│   ├── prompt_v2.md         # Extended feature specification
│   ├── README.md            # Snake game documentation
│   ├── highscore.txt        # Generated high-score data
│   └── settings.txt         # Generated game settings
│
├── pyproject.toml           # Project configuration & dependencies
├── uv.lock                  # Locked dependency versions
├── .env.example             # Environment variable template
├── .gitignore               # Git exclusions
└── README.md                # Project documentation
```

---

## 🧰 Tech Stack

* **Python**
* **OpenAI Python SDK**
* **OpenRouter API**
* **LLM Tool Calling**
* **JSON Schema**
* **Subprocess**
* **python-dotenv**
* **uv**
* **Pygame** — for the generated Snake game

---

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/builtbyrehan/agent-tool-calling.git
cd agent-tool-calling
```

### 2. Install Dependencies

This project uses `uv`.

```bash
uv sync
```

### 3. Configure Your API Key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

The project uses the OpenAI Python SDK with OpenRouter as the API endpoint.

**Never commit your `.env` file.**

### 4. Run the Agent

```bash
uv run python agent.py
```

You should see:

```text
Mini agent ready. Type exit to quit.
```

You can now give the agent tasks such as:

```text
Create a Python calculator application.
```

or:

```text
Inspect the snake_game directory and explain the project.
```

or:

```text
Add a new feature to the Snake game.
```

---

## 🎮 Snake Game Documentation

The complete documentation for the generated game is available in:

[`snake_game/README.md`](snake_game/README.md)

The main game implementation is:

[`snake_game/snake_game.py`](snake_game/snake_game.py)

The development specifications used during the process are:

* [`snake_game/prompt.txt`](snake_game/prompt.txt)
* [`snake_game/prompt_v2.md`](snake_game/prompt_v2.md)

This makes the repository useful not only as an agent demonstration, but also as an example of the **software artifact produced through tool-using interaction**.

---

## 📚 What I Learned

Building this project helped me understand the practical relationship between **LLMs, APIs, tools, and agent loops**.

### LLM APIs

How an application communicates with an LLM through an API and sends conversation history to the model.

### Tool Calling

How an LLM can request actions instead of only returning text.

### JSON Schemas

Why tools need structured descriptions containing:

* Tool names
* Descriptions
* Parameters
* Required arguments

### Tool Execution

How the Python application maps the model's requested tool to an actual Python function.

### Agent Loops

How tool results can be returned to the model so it can decide what to do next.

### Human-in-the-Loop

Why human approval becomes important when agents receive access to real system resources.

---

## 💡 Key Insight

A traditional chatbot mainly follows:

```text
User → LLM → Response
```

A tool-using agent can follow:

```text
User
  ↓
LLM
  ↓
Tool Call
  ↓
External Environment
  ↓
Tool Result
  ↓
LLM
  ↓
Next Action
```

The important shift is that the LLM is no longer limited to producing text.

It can **request actions, observe their results, and use those results to determine what to do next.**

> **LLM + Tools + Environment + Feedback Loop = Agentic Workflow**

---

## 🚀 Future Improvements

* [ ] Add stronger command validation
* [ ] Restrict file-system access to a sandbox
* [ ] Add command allowlists
* [ ] Add more specialized development tools
* [ ] Improve error handling
* [ ] Add conversation memory
* [ ] Add structured logging
* [ ] Add automated tests
* [ ] Add better permission controls
* [ ] Build a web interface
* [ ] Add agent planning / task decomposition
* [ ] Add tool execution history
* [ ] Add support for multiple LLM providers

---

## ⚠️ Security Notice

This project is designed for **learning and experimentation**.

The agent can interact with the filesystem and execute shell commands. Do not run it in directories or environments where unintended changes could cause damage.

The current human approval mechanism is a **basic guardrail**, not a complete security boundary.

A production implementation would require stronger isolation, validation, permissions, and sandboxing.

---

## ⭐ Key Takeaway

This project started as an experiment to understand **LLM tool calling** and evolved into a small coding agent capable of interacting with a real development environment.

The most important lesson was:

> **An LLM becomes significantly more useful as an agent when it can interact with tools, observe the results, and continue acting based on those results.**

---

## 👨‍💻 Author

**Rehan**

Built as part of my journey into **LLM Engineering, Agentic AI, and AI Systems Engineering**.

GitHub: [@builtbyrehan](https://github.com/builtbyrehan)

---

## 📄 License

This project is intended for educational and experimental purposes.

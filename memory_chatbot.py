from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os 
load_dotenv
print("API Key loaded:", os.getenv("OPENAI_API_KEY"))
load_dotenv(Path(__file__).parent / ".env") # due to some reason .env was not locating we used Path to locate .env explicitly 
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url="https://openrouter.ai/api/v1")

isTrue = True
messages = []
print("Welcome to Agent!\n Type exit to leave. Thank-you:)")
while isTrue:
    user_input = input("You: ")

    if (user_input == "exit"): 
        print("GoodBye!")
        break; 
    messages.append({"role": "user","content": user_input})
    response = client.chat.completions.create(
        model =  "minimax/minimax-m3:free",
        messages=messages
    )
    agent_reply = response.choices[0].message.content
    print("Agent: ",agent_reply,"\n")

    messages.append({"role": "assistant","content": agent_reply})

    # print("The full conversation data: ")
    # print("="* 50)
    # print(messages)
    # print("=" *50)

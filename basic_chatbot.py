from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url = "https://openrouter.ai/api/v1")
# client made






response = client.chat.completions.create(
    model = "minimax/minimax-m3:free",
    messages=[{"role": "user","content" : "Hey tell me about PUBG."}]
    

)

print(response.choices[0].message.content)
from groq import Groq
from config.config import Config

client = Groq(api_key=Config.GROQ_API_KEY)

def get_bot_response(user_message):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": user_message}],
        model="llama3-8b-8192",
    )
    return chat_completion.choices[0].message.content
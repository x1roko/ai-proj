import os
from dotenv import load_dotenv
from groq import Groq
from config.config import Config
import logging
from typing import List, Dict

# Загружаем .env файл
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем ключ API
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY не найден в переменных окружения")

client = Groq(api_key=GROQ_API_KEY)

def get_bot_response(user_message):
    try:
        logger.info(f"Sending message to Groq API: {user_message[:50]}...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Ты - русскоязычный AI-ассистент. Общайся на русском языке, соблюдая следующие правила:
                    1. Отвечай на русском языке, используя правильную грамматику и пунктуацию
                    2. Сохраняй технические термины, названия библиотек, и код на английском
                    3. Код должен оставаться в оригинальном виде внутри блоков ```
                    4. Примеры использования и документацию оставляй на английском, если это важно для точности
                    5. Будь вежливым и профессиональным в общении"""
                },
                {"role": "user", "content": user_message}
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=2048,
            stream=True
        )
        
        for chunk in chat_completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"Error in get_bot_response: {str(e)}")
        yield f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}"
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

def get_bot_response(user_message, previous_messages=None):
    try:
        logger.info(f"Sending message to Groq API: {user_message[:50]}...")
        
        # Формируем системное сообщение с четкими инструкциями
        messages = [
            {
                "role": "system",
                "content": """Ты - русскоязычный AI-ассистент. Продолжай диалог, соблюдая следующие правила:
                1. Отвечай на русском языке, используя правильную грамматику и пунктуацию
                2. Сохраняй технические термины, названия библиотек, и код на английском
                3. Код должен оставаться в оригинальном виде внутри блоков ```
                4. Примеры использования и документацию оставляй на английском, если это важно для точности
                5. Будь вежливым и профессиональным в общении
                6. Начинай ответ с 'Бот:' только один раз
                7. Используй маркированные списки и форматирование для лучшей читаемости
                8. Не дублируй префикс 'Бот:' в ответах"""
            }
        ]
        
        # Форматируем предыдущие сообщения
        if previous_messages:
            formatted_messages = []
            for msg in previous_messages:
                if msg["role"] == "user":
                    formatted_messages.append({
                        "role": "user",
                        "content": f"Вы: {msg['content']}"
                    })
                else:
                    content = msg['content']
                    if content.startswith("Бот: Бот:"):
                        content = content.replace("Бот: Бот:", "Бот:", 1)
                    elif not content.startswith("Бот:"):
                        content = f"Бот: {content}"
                    formatted_messages.append({
                        "role": "assistant",
                        "content": content
                    })
            messages.extend(formatted_messages)
        
        # Добавляем текущее сообщение пользователя
        messages.append({
            "role": "user",
            "content": f"Вы: {user_message}"
        })
        
        logger.info(f"Sending context with {len(messages)} messages")
        
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=2048,
            stream=True
        )
        
        response_started = False
        full_response = ""
        
        for chunk in chat_completion:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                
                if not response_started:
                    # Проверяем и корректируем начало ответа
                    if content.startswith("Бот: Бот:"):
                        content = content.replace("Бот: Бот:", "Бот:", 1)
                    elif not content.startswith("Бот:"):
                        content = "Бот: " + content
                    response_started = True
                
                full_response += content
                yield content

    except Exception as e:
        logger.error(f"Error in get_bot_response: {str(e)}")
        yield f"Бот: Извините, произошла ошибка при обработке вашего запроса: {str(e)}"
from dotenv import load_dotenv
from app import create_app
from config.config import Config
import os
import sys

# Получаем абсолютный путь к директории текущего файла
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')

# Проверяем существование файла .env
if not os.path.exists(env_path):
    print(f"Файл .env не найден по пути: {env_path}")
    sys.exit(1)

# Загружаем переменные окружения из .env файла
load_dotenv(env_path, override=True)

# Выводим для отладки
print("Текущая директория:", current_dir)
print("Путь к .env:", env_path)
print("GROQ_API_KEY из os.environ:", os.environ.get('GROQ_API_KEY'))
print("GROQ_API_KEY из os.getenv:", os.getenv('GROQ_API_KEY'))

# Явно устанавливаем значение в Config
Config.GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Проверяем конфигурацию
try:
    Config.validate_config()
except ValueError as e:
    print(f"Ошибка конфигурации: {e}")
    sys.exit(1)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
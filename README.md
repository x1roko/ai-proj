# AI Chat Application

Веб-приложение для общения с AI-ассистентом, построенное на Flask с поддержкой как анонимного чата (через сессии), так и авторизованного доступа (через JWT).

## Функциональность

- Анонимный чат с сохранением истории в сессии
- Регистрация и авторизация пользователей
- Сохранение истории чата в базе данных для авторизованных пользователей
- Интеграция с Groq AI API
- Responsive дизайн

## Технологии

- Python 3.8+
- Flask
- Flask-JWT-Extended
- SQLite3
- Groq API
- HTML/CSS/JavaScript

## Установка и запуск

1. Клонируйте репозиторий:

bash
git clone https://github.com/your-xiroko/ai-proj.git
cd ai-proj


2. Создайте виртуальное окружение и активируйте его:

bash
python -m venv venv
source venv/bin/activate

3. Установите зависимости:

bash
pip install -r requirements.txt

4. Создайте файл .env и добавьте в него необходимые переменные окружения:

bash
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
GROQ_API_KEY=your-groq-api-key


5. Инициализируйте базу данных:

bash
flask init-db


6. Запустите приложение:
bash
python run.py
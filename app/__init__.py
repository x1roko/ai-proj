from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from config.config import Config
from app.models.database import init_db
import os
from dotenv import load_dotenv

# Загружаем .env файл до создания приложения
load_dotenv()

def create_app(test_config=None):
    # Создаем приложение с правильным путем к шаблонам
    app = Flask(__name__,
                template_folder='templates',  # Указываем папку с шаблонами
                static_folder='static',       # Указываем папку со статическими файлами
                static_url_path='/ai/static')  # Указываем префикс для статики
    
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.update(test_config)

    # Убедимся, что папка instance существует
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Инициализация JWT
    jwt = JWTManager(app)

    # Инициализация базы данных
    with app.app_context():
        init_db()

    # Регистрация Blueprint'ов
    from app.routes import auth, chat
    app.register_blueprint(auth.bp, url_prefix='/ai/api/auth')
    app.register_blueprint(chat.bp, url_prefix='/ai/api/chat')

    @app.route('/ai/')
    def index():
        return render_template('index.html')

    return app
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'chat.sqlite')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    APPLICATION_ROOT = '/ai'
    PREFERRED_URL_SCHEME = 'https'
    
    # GROQ API ключ
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    @classmethod
    def validate_config(cls):
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY не найден! Пожалуйста, установите переменную окружения GROQ_API_KEY"
            )
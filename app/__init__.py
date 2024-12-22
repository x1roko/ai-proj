from flask import Flask
from flask_jwt_extended import JWTManager
from config.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    jwt = JWTManager(app)
    
    from app.routes import auth, chat
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    
    return app
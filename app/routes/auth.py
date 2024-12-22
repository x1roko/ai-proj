from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.database import get_db
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone() is not None:
            return jsonify({'error': 'User already exists'}), 400

        cursor.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        db.commit()

        user_id = cursor.lastrowid
        access_token = create_access_token(
            identity=username,
            expires_delta=datetime.timedelta(days=30)
        )

        cursor.execute(
            'INSERT INTO tokens (user_id, token) VALUES (?, ?)',
            (user_id, access_token)
        )
        db.commit()

        return jsonify({
            'access_token': access_token,
            'username': username
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid username or password'}), 401

        access_token = create_access_token(
            identity=username,
            expires_delta=datetime.timedelta(days=30)
        )

        cursor.execute(
            'INSERT INTO tokens (user_id, token) VALUES (?, ?)',
            (user['id'], access_token)
        )
        db.commit()

        return jsonify({
            'access_token': access_token,
            'username': username
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/validate-token', methods=['GET'])
@jwt_required()
def validate_token():
    try:
        current_user = get_jwt_identity()
        
        # Проверяем существование пользователя в базе
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (current_user,))
        user = cursor.fetchone()
        
        if user is None:
            # Если пользователь не найден, возвращаем ошибку
            logger.warning(f"User {current_user} not found in database")
            return jsonify({
                'valid': False,
                'error': 'User not found'
            }), 401
            
        return jsonify({
            'valid': True,
            'username': current_user
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 401
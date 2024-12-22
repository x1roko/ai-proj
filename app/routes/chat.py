from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.database import get_db
from app.utils.chat_helper import get_bot_response

bp = Blueprint('chat', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    response_message = get_bot_response(user_message)

    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append({
        'user_message': user_message,
        'bot_response': response_message
    })
    
    return jsonify({'response': response_message})

@bp.route('/chat-auth', methods=['POST'])
@jwt_required()
def chat_auth():
    user_message = request.json.get('message')
    username = get_jwt_identity()
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    response_message = get_bot_response(user_message)

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO messages (user_id, user_message, bot_response)
        VALUES (?, ?, ?)
    ''', (username, user_message, response_message))
    db.commit()
    
    return jsonify({'response': response_message})

@bp.route('/history', methods=['GET'])
def session_history():
    return jsonify({'messages': session.get('chat_history', [])})

@bp.route('/history-auth', methods=['GET'])
@jwt_required()
def db_history():
    username = get_jwt_identity()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_message, bot_response FROM messages WHERE user_id = ?', (username,))
    messages = cursor.fetchall()

    return jsonify({'messages': [{'user_message': msg[0], 'bot_response': msg[1]} for msg in messages]})
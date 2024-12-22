from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models.database import get_db
from app.utils.chat_helper import get_bot_response
import json
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('chat', __name__, url_prefix='/api/chat')

def get_user_id(username):
    if not username:
        return None
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    return result[0] if result else None

@bp.route('/chat', methods=['POST'])
def chat():
    try:
        # Пробуем получить токен, но не требуем его
        try:
            verify_jwt_in_request(optional=True)
        except Exception as e:
            logger.info(f"No valid JWT token: {str(e)}")

        user_message = request.json.get('message')
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        current_user = get_jwt_identity()
        user_id = get_user_id(current_user) if current_user else None
        
        if not user_id and 'anonymous_id' not in session:
            session['anonymous_id'] = str(uuid.uuid4())
            session.modified = True

        logger.info(f"Processing message from user {current_user or 'anonymous'}")

        def generate():
            try:
                response_text = ""
                for token in get_bot_response(user_message):
                    response_text += token
                    yield f"data: {json.dumps({'token': token, 'full_response': response_text})}\n\n"

                db = get_db()
                with db:
                    cursor = db.cursor()
                    if user_id:
                        cursor.execute('''
                            INSERT INTO chat_history (user_id, user_message, bot_response)
                            VALUES (?, ?, ?)
                        ''', (user_id, user_message, response_text))
                    else:
                        cursor.execute('''
                            INSERT INTO chat_history (session_id, user_message, bot_response)
                            VALUES (?, ?, ?)
                        ''', (session.get('anonymous_id'), user_message, response_text))

            except Exception as e:
                logger.error(f"Error in generate: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/chat-auth', methods=['POST'])
@jwt_required()
def chat_auth():
    try:
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
    except Exception as e:
        print(f"Error in chat_auth route: {str(e)}")  # для отладки
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/history', methods=['GET'])
def get_history():
    try:
        try:
            verify_jwt_in_request(optional=True)
        except Exception as e:
            logger.info(f"No valid JWT token: {str(e)}")

        current_user = get_jwt_identity()
        user_id = get_user_id(current_user) if current_user else None
        
        db = get_db()
        cursor = db.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT user_message, bot_response 
                FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp ASC
            ''', (user_id,))
        else:
            session_id = session.get('anonymous_id')
            if not session_id:
                return jsonify({'history': []})
            
            cursor.execute('''
                SELECT user_message, bot_response 
                FROM chat_history 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            ''', (session_id,))
        
        history = [
            {'user_message': row[0], 'bot_response': row[1]}
            for row in cursor.fetchall()
        ]
        
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        try:
            verify_jwt_in_request(optional=True)
        except Exception as e:
            logger.info(f"No valid JWT token: {str(e)}")

        current_user = get_jwt_identity()
        user_id = get_user_id(current_user) if current_user else None
        
        db = get_db()
        cursor = db.cursor()
        
        if user_id:
            cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
        else:
            session_id = session.get('anonymous_id')
            if session_id:
                cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
        
        db.commit()
        return jsonify({'message': 'История чата очищена'})
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/history-auth', methods=['GET'])
@jwt_required()
def db_history():
    username = get_jwt_identity()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_message, bot_response FROM messages WHERE user_id = ?', (username,))
    messages = cursor.fetchall()

    return jsonify({'messages': [{'user_message': msg[0], 'bot_response': msg[1]} for msg in messages]})
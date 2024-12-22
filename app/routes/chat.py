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
        logger.info("Starting chat request processing")
        
        # Пробуем получить токен, но не требуем его
        try:
            verify_jwt_in_request(optional=True)
        except Exception as e:
            logger.info(f"No valid JWT token: {str(e)}")

        user_message = request.json.get('message')
        if not user_message:
            logger.error("No message provided in request")
            return jsonify({'error': 'Message is required'}), 400

        current_user = get_jwt_identity()
        logger.info(f"Current user: {current_user}")
        
        user_id = get_user_id(current_user) if current_user else None
        logger.info(f"User ID: {user_id}")
        
        if not user_id and 'anonymous_id' not in session:
            session['anonymous_id'] = str(uuid.uuid4())
            session.modified = True
            logger.info(f"Created new anonymous session: {session['anonymous_id']}")

        def generate():
            try:
                logger.info("Starting message generation")
                response_text = ""
                
                # Инициализируем базу данных и курсор
                db = get_db()
                cursor = db.cursor()
                logger.info("Database connection established")
                
                # Получаем предыдущие сообщения для контекста
                previous_messages = []
                try:
                    if user_id:
                        logger.info(f"Fetching history for user_id: {user_id}")
                        cursor.execute('''
                            SELECT user_message, bot_response 
                            FROM chat_history 
                            WHERE user_id = ? 
                            ORDER BY timestamp ASC
                            LIMIT 10
                        ''', (user_id,))
                    else:
                        session_id = session.get('anonymous_id')
                        logger.info(f"Fetching history for session_id: {session_id}")
                        if session_id:
                            cursor.execute('''
                                SELECT user_message, bot_response 
                                FROM chat_history 
                                WHERE session_id = ? 
                                ORDER BY timestamp ASC
                                LIMIT 10
                            ''', (session_id,))
                    
                    # Получаем результаты запроса
                    history_rows = cursor.fetchall()
                    logger.info(f"Found {len(history_rows)} previous messages")
                    
                    for row in history_rows:
                        previous_messages.append({"role": "user", "content": row[0]})
                        previous_messages.append({"role": "assistant", "content": row[1]})
                
                except Exception as db_error:
                    logger.error(f"Database error: {str(db_error)}")
                    yield f"data: {json.dumps({'error': f'Database error: {str(db_error)}'})}\n\n"
                    return

                try:
                    logger.info("Starting bot response generation")
                    for token in get_bot_response(user_message, previous_messages):
                        response_text += token
                        try:
                            # Экранируем специальные символы только для JSON
                            safe_token = token.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                            yield f"data: {json.dumps({'token': safe_token, 'full_response': response_text})}\n\n"
                        except Exception as json_error:
                            logger.error(f"JSON encoding error: {str(json_error)} for token: {token}")
                            # В случае ошибки пропускаем проблемный токен
                            continue
                    logger.info("Bot response generation completed")
                
                except Exception as bot_error:
                    logger.error(f"Bot response error: {str(bot_error)}")
                    yield f"data: {json.dumps({'error': f'Bot response error: {str(bot_error)}'})}\n\n"
                    return

                try:
                    logger.info("Saving message to database")
                    with db:
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
                    logger.info("Message saved successfully")
                
                except Exception as save_error:
                    logger.error(f"Error saving to database: {str(save_error)}")
                    yield f"data: {json.dumps({'error': f'Error saving message: {str(save_error)}'})}\n\n"

            except Exception as e:
                logger.error(f"General error in generate: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        logger.info("Returning response stream")
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

@bp.route('/clear-history', methods=['POST'])
def clear_history():
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

@bp.route('/history-auth', methods=['GET'])
@jwt_required()
def db_history():
    username = get_jwt_identity()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_message, bot_response FROM messages WHERE user_id = ?', (username,))
    messages = cursor.fetchall()

    return jsonify({'messages': [{'user_message': msg[0], 'bot_response': msg[1]} for msg in messages]})
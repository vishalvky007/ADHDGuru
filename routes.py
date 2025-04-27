from flask import request, jsonify, Response, render_template
from datetime import datetime
from bson.objectid import ObjectId

# Import utilities
from ai_utils import detect_tone, classify_user, get_ai_response, generate_title
from models import chats_collection, messages_collection, journal_collection, using_fallback

def is_valid_object_id(id_string):
    """Check if the string can be converted to ObjectId"""
    try:
        ObjectId(id_string)
        return True
    except:
        return False

def register_routes(app):
    # Main routes
    @app.route("/")
    def index():
        return render_template("index.html")
        
    @app.route("/features")
    def features():
        return render_template("features.html")
        
    # Chat routes
    @app.route('/api/chat/start', methods=['POST'])
    def start_chat():
        try:
            user_id = request.json.get('user_id', 'anonymous_user')
            
            # Create a new chat session
            chat_session = {
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True
            }
            
            chat_id = chats_collection.insert_one(chat_session).inserted_id
            
            return jsonify({
                'status': 'success',
                'chat_id': str(chat_id)
            }), 200
            
        except Exception as e:
            app.logger.error(f"Error starting chat: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f"Failed to start chat session: {str(e)}"
            }), 500

    @app.route('/api/chat/message', methods=['POST'])
    def send_message():
        try:
            data = request.json
            chat_id = data.get('chat_id')
            user_id = data.get('user_id', 'anonymous_user')
            message = data.get('message')
            
            if not chat_id or not message:
                return jsonify({
                    'status': 'error',
                    'message': 'chat_id and message are required'
                }), 400
            
            # Save user message
            user_message = {
                'chat_id': chat_id,
                'user_id': user_id,
                'content': message,
                'role': 'user',
                'timestamp': datetime.utcnow()
            }
            messages_collection.insert_one(user_message)
            
            # Update chat session
            query = {'_id': ObjectId(chat_id) if is_valid_object_id(chat_id) else chat_id}
            chats_collection.update_one(
                query,
                {'$set': {'updated_at': datetime.utcnow()}}
            )
            
            # Get chat history (only get last few messages to avoid context window issues)
            chat_history = list(messages_collection.find({
                'chat_id': chat_id
            }).sort('timestamp', 1).limit(10))
            
            # Get response from model with streaming
            app.logger.info(f"Getting AI response for message: {message[:30]}...")
            response = get_ai_response(message, chat_history)
            
            # Process the streamed response
            def generate():
                full_response = ""
                try:
                    for chunk in response:
                        if hasattr(chunk, 'text') and chunk.text:
                            full_response += chunk.text
                            yield chunk.text
                        elif isinstance(chunk, str):
                            full_response += chunk
                            yield chunk
                            
                    # Save the AI response after streaming is complete
                    if full_response:
                        ai_message = {
                            'chat_id': chat_id,
                            'user_id': 'ai',
                            'content': full_response,
                            'role': 'assistant',
                            'timestamp': datetime.utcnow()
                        }
                        messages_collection.insert_one(ai_message)
                except Exception as e:
                    app.logger.error(f"Error streaming response: {str(e)}")
                    yield f"\n\nError: {str(e)}"
            
            return Response(generate(), mimetype='text/plain')
            
        except Exception as e:
            app.logger.error(f"Error processing message: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f"Failed to process message: {str(e)}"
            }), 500

    @app.route('/api/chat/history', methods=['GET'])
    def get_chat_history():
        try:
            chat_id = request.args.get('chat_id')
            
            if not chat_id:
                return jsonify({
                    'status': 'error',
                    'message': 'chat_id is required'
                }), 400
            
            # Get messages for the chat
            messages = messages_collection.find({
                'chat_id': chat_id
            }).sort('timestamp', 1)
            
            # Format messages
            formatted_messages = []
            for msg in messages:
                # Convert ObjectId to string if needed
                if hasattr(msg.get('_id'), 'to_string'):
                    msg['_id'] = str(msg['_id'])
                    
                # Format timestamp
                if isinstance(msg.get('timestamp'), datetime):
                    timestamp = msg['timestamp'].isoformat()
                else:
                    timestamp = str(msg.get('timestamp', ''))
                
                formatted_messages.append({
                    'content': msg.get('content', ''),
                    'role': msg.get('role', 'unknown'),
                    'timestamp': timestamp
                })
            
            return jsonify({
                'status': 'success',
                'messages': formatted_messages
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # Journal routes
    @app.route('/api/journal/entries', methods=['GET'])
    def get_journal_entries():
        try:
            entries = list(journal_collection.find().sort('date', -1))
            # Convert ObjectId to string for JSON serialization
            for entry in entries:
                if hasattr(entry.get('_id'), 'to_string'):
                    entry['_id'] = str(entry['_id'])
                else:
                    entry['_id'] = str(entry.get('_id', ''))
            return jsonify({
                'status': 'success',
                'entries': entries
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/journal/entry', methods=['POST'])
    def create_journal_entry():
        try:
            data = request.json
            entry = {
                'title': data.get('title'),
                'content': data.get('content'),
                'date': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = journal_collection.insert_one(entry)
            entry['_id'] = str(result.inserted_id)
            
            return jsonify({
                'status': 'success',
                'entry': entry
            }), 201
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/journal/entry/<entry_id>', methods=['PUT'])
    def update_journal_entry(entry_id):
        try:
            data = request.json
            update_data = {
                'title': data.get('title'),
                'content': data.get('content'),
                'updated_at': datetime.utcnow()
            }
            
            # Use ObjectId only if it's a valid format and we're not using fallback
            id_query = {'_id': ObjectId(entry_id) if is_valid_object_id(entry_id) and not using_fallback else entry_id}
            
            result = journal_collection.update_one(
                id_query,
                {'$set': update_data}
            )
            
            if result.modified_count == 0:
                return jsonify({
                    'status': 'error',
                    'message': 'Entry not found'
                }), 404
                
            return jsonify({
                'status': 'success',
                'message': 'Entry updated successfully'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/journal/entry/<entry_id>', methods=['DELETE'])
    def delete_journal_entry(entry_id):
        try:
            # Use ObjectId only if it's a valid format and we're not using fallback
            id_query = {'_id': ObjectId(entry_id) if is_valid_object_id(entry_id) and not using_fallback else entry_id}
            
            result = journal_collection.delete_one(id_query)
            
            if result.deleted_count == 0:
                return jsonify({
                    'status': 'error',
                    'message': 'Entry not found'
                }), 404
                
            return jsonify({
                'status': 'success',
                'message': 'Entry deleted successfully'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/journal/generate-title', methods=['POST'])
    def generate_journal_title():
        try:
            content = request.json.get('content')
            if not content:
                return jsonify({
                    'status': 'error',
                    'message': 'Content is required'
                }), 400

            title = generate_title(content)
            
            return jsonify({
                'status': 'success',
                'title': title
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500


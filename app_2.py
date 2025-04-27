from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from pymongo import MongoClient
import google.generativeai as genai
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure MongoDB
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    print("WARNING: No MONGO_URI found in .env file. Using default local MongoDB connection without authentication.")
    MONGO_URI = 'mongodb://localhost:27017/'
else:
    print(f"Connected to MongoDB with URI from .env file")

client = MongoClient(MONGO_URI)
db = client['chatbot_db']
chats_collection = db['chats']
messages_collection = db['messages']
journal_collection = db['journal_entries']

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

def detect_tone(user_input):
    score = analyzer.polarity_scores(user_input)
    if score['compound'] >= 0.05:
        return "positive"
    elif score['compound'] <= -0.05:
        return "negative"
    else:
        return "neutral"

def classify_user(user_input):
    user_input = user_input.lower()
    if "parent" in user_input:
        return "Parent of an ADHD child"
    elif "teacher" in user_input or "educator" in user_input:
        return "Teacher/Educator working with ADHD students"
    elif "employer" in user_input:
        return "Employer managing an ADHD employee"
    elif "adhd" in user_input or "adult" in user_input:
        return "Adult with ADHD"
    else:
        return "General user (uncategorized)"

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    try:
        user_id = request.json.get('user_id')
        
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/chat/message', methods=['POST'])
def send_message():
    try:
        data = request.json
        chat_id = data.get('chat_id')
        user_id = data.get('user_id')
        message = data.get('message')
        
        # Get chat history
        chat_history = messages_collection.find({
            'chat_id': chat_id
        }).sort('timestamp', 1)
        
        # Detect tone and user type
        tone = detect_tone(message)
        user_category = classify_user(message)
        
        # Prepare system prompt
        system_prompt = f"""
        You are an ADHD support chatbot with the personality of a warm, supportive counselor. 
        Your job is to provide clear, concise, and structured guidance to users based on their needs.

        User type: {user_category}

        - If they are an ADHD adult, offer self-management strategies.
        - If they are a parent, provide parenting tips.
        - If they are a teacher, suggest ADHD-friendly teaching techniques.
        - If they are an employer, recommend workplace accommodations.
        """
        
        # Initialize chat with history
        chat = model.start_chat(history=[])
        
        # Add system prompt
        chat.send_message(system_prompt)
        
        # Add previous messages to context
        for msg in chat_history:
            chat.send_message(msg['content'])
        
        # Get response from model with streaming
        response = chat.send_message(message, stream=True)
        
        def generate():
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
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
        chats_collection.update_one(
            {'_id': chat_id},
            {'$set': {'updated_at': datetime.utcnow()}}
        )
        
        return Response(generate(), mimetype='text/plain')
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    try:
        chat_id = request.args.get('chat_id')
        
        # Get messages for the chat
        messages = messages_collection.find({
            'chat_id': chat_id
        }).sort('timestamp', 1)
        
        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'content': msg['content'],
                'role': msg['role'],
                'timestamp': msg['timestamp'].isoformat()
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

@app.route('/api/journal/entries', methods=['GET'])
def get_journal_entries():
    try:
        entries = list(journal_collection.find().sort('date', -1))
        # Convert ObjectId to string for JSON serialization
        for entry in entries:
            entry['_id'] = str(entry['_id'])
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
        
        result = journal_collection.update_one(
            {'_id': ObjectId(entry_id)},
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
        result = journal_collection.delete_one({'_id': ObjectId(entry_id)})
        
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
def generate_title():
    try:
        content = request.json.get('content')
        if not content:
            return jsonify({
                'status': 'error',
                'message': 'Content is required'
            }), 400

        # Use Gemini to generate a title
        prompt = f"""
        Generate a concise, meaningful title (maximum 5 words) for this journal entry:
        {content}
        
        Return only the title, nothing else.
        """
        
        response = model.generate_content(prompt)
        title = response.text.strip()
        
        return jsonify({
            'status': 'success',
            'title': title
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
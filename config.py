import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'chatbot_db'

# Collection names
CHATS_COLLECTION = 'chats'
MESSAGES_COLLECTION = 'messages'
JOURNAL_COLLECTION = 'journal_entries'

# Google Generative AI
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MODEL_NAME = 'gemini-1.5-flash-latest'

# Flask Configuration
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
PORT = int(os.getenv('PORT', 5000)) 
# ADHDGuru

ADHDGuru is an AI-powered chatbot designed to provide personalized guidance and support for ADHD and autism-related challenges.

## Project Structure

The project follows a modular approach:

- `config.py` - Contains all configuration variables
- `models.py` - Sets up database connections and collections
- `ai_utils.py` - Provides AI-related functionality (sentiment analysis, user classification, etc.)
- `routes.py` - Contains all application routes organized by feature
- `app.py` - Creates the Flask application
- `run.py` - Entry point to run the application

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with the following variables:
   ```
   MONGO_URI=your_mongodb_connection_string
   GOOGLE_API_KEY=your_google_api_key
   DEBUG=True
   PORT=5000
   ```

## Running the Application

To run the application, use:

```bash
python run.py
```

This will start the server on the port specified in your `.env` file (default: 5000).

## Features

- **AI-Powered Support**: Utilizes Google's Gemini AI for personalized guidance and support
- **Role-Based Adaptation**: Tailored strategies for adults with ADHD/autism, parents, teachers, and employers
- **Chatbot Interface**: Natural language interaction for asking questions and receiving guidance
- **Journal**: Ability to create and manage journal entries with AI-generated titles 
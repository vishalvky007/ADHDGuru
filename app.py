from flask import Flask
from flask_cors import CORS
from config import DEBUG, PORT
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
def create_app():
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configure CORS - instead of using the extension
    app.config['CORS_HEADERS'] = 'Content-Type'
    
    # Import routes after app is created to avoid circular imports
    from routes import register_routes
    register_routes(app)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        app.logger.error(f"404 error: {error}")
        return "Not Found", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        return "Internal Server Error", 500
    
    return app

# Create the app instance
app = create_app()

# Add CORS support
CORS(app)

# This is only used when running app.py directly
if __name__ == '__main__':
    app.logger.info(f"Starting server in {'DEBUG' if DEBUG else 'PRODUCTION'} mode on port {PORT}")
    app.run(debug=DEBUG, port=PORT, host='0.0.0.0') 
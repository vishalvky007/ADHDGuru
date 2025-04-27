from app import create_app  # suppose you have a factory
from config import DEBUG, PORT

app = create_app()

if __name__ == "__main__":
    print(f"Starting ADHDGuru server in {'debug' if DEBUG else 'production'} mode on port {PORT}")
    app.run(debug=DEBUG, port=PORT)

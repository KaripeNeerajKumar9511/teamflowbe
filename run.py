"""
Entry point for the Flask development server.
Run with:  python run.py
"""
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env before anything else

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

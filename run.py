"""
Entry point for the Flask development server.
Run with: python run.py
"""

from dotenv import load_dotenv
load_dotenv()

import os
from flask_cors import CORS
from app import create_app

app = create_app()

CORS(app)

@app.route("/")
def home():
    return "Backend is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
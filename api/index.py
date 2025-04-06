from flask import Flask, request, jsonify
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app from the parent directory
from app import app as flask_app

# This is necessary for Vercel serverless deployment
app = flask_app

# Import webhook functionality
from api.webhook import *

# Add a simple status endpoint for health checks
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "message": "Bot API is running"
    })

# If this file is run directly, start the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

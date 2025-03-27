from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from flask_cors import CORS
import uuid
import os
from dotenv import load_dotenv

from models import Base, engine
from db_tool import store_chat_history, get_chat_history_for_user
from chatbot import generate_response

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///database.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SWAGGER'] = {'title': 'Chatbot API', 'uiversion': 3}

db = SQLAlchemy(app)
Swagger(app)
CORS(app)

Base.metadata.bind = engine

@app.route('/chat', methods=['POST'])
def chat():
    """
    Send a message to the chatbot
    ---
    parameters:
      - in: body
        name: payload
        schema:
          type: object
          properties:
            user_id:
              type: integer
            user_name:
              type: string
            session_id:
              type: string
            message:
              type: string
            role:
              type: string
        required:
          - user_id
          - user_name
          - message
          - role
    responses:
      200:
        description: Chat response with session ID and bot response.
    """
    data = request.get_json()
    user_id = int(data.get('user_id'))
    user_name = data.get('user_name')
    session_id = data.get('session_id') or str(uuid.uuid4())
    message = data.get('message')
    role = data.get('role')
    
    bot_response = generate_response(message, role, logged_in_user=user_name, conversation_session_id=session_id)
    session_id = store_chat_history(user_id, message, "user", session_id)
    store_chat_history(user_id, bot_response, "bot", session_id)
    
    return jsonify({"session_id": session_id, "bot_response": bot_response})

@app.route('/chat/history/<int:user_id>', methods=['GET'])
def chat_history(user_id):
    """
    Retrieve chat history for a user
    ---
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: List of chat messages.
    """
    history = get_chat_history_for_user(user_id)
    return jsonify(history)

if __name__ == '__main__':
    with app.app_context():
        Base.metadata.create_all(engine)
    app.run(debug=True)

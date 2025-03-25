# backend/routes/chatbot.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

chatbot_bp = Blueprint("chatbot_bp", __name__)

@chatbot_bp.route('/', methods=['POST'])
@jwt_required()
def chatbot_query():
    data = request.get_json()
    role = data.get("role")  # This can be used to customize responses
    query = data.get("query")
    
    # Simple stub logic: respond based on role
    if role == "HR":
        response = f"HR Chatbot: Received your query '{query}' for company-wide insights."
    elif role == "Manager":
        response = f"Manager Chatbot: Your team data for query '{query}' is being processed."
    else:
        response = f"Employee Chatbot: Here is your personal info for '{query}'."
    
    return jsonify({"response": response}), 200

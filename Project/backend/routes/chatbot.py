# backend/routes/chatbot.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from chatbot_llm import generate_response
from models import User, SessionLocal

chatbot_bp = Blueprint("chatbot_bp", __name__)


def get_logged_in_user_name():
    current_user_id = get_jwt_identity()
    session = SessionLocal()
    user = session.query(User).get(current_user_id)
    
    if user:
        return f"{user.first_name} {user.last_name}"
    
    session.close()
    return None


@chatbot_bp.route('/', methods=['POST'])
@jwt_required()
def chatbot_query():
    try:
        data = request.get_json()
        
        # ✅ Log received data for debugging
        print("Received JSON:", data)

        if not data:
            return jsonify({"msg": "Invalid or missing JSON payload"}), 400

        role = data.get("role")
        query = data.get("query")

        if not role or not query:
            return jsonify({"msg": "Missing 'role' or 'query' field"}), 400

        # ✅ Ensure role is a valid string
        role = role.strip().lower()

        # ✅ Get logged-in user name
        user_name = get_logged_in_user_name()
        if not user_name:
            return jsonify({"msg": "User not found"}), 404

        # ✅ Call chatbot function
        response_text = generate_response(query, role, user_name)

        return jsonify({"response": response_text}), 200
    except Exception as e:
        return jsonify({"msg": f"Error processing request: {str(e)}"}), 500

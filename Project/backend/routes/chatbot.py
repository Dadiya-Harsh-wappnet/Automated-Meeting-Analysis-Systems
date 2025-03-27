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
        # ✅ Debugging: Print raw request data
        print("🔹 Raw Request Data:", request.data)

        # ✅ Debugging: Print JSON content before using it
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"msg": "Invalid or missing JSON payload"}), 400  # Return 400 instead of 422

        print("📩 Parsed JSON:", data)

        role = data.get("role")
        query = data.get("query")

        # ✅ Debugging: Check if role and query exist
        print(f"📝 Role: {role} | Query: {query} | Type: {type(query)}")

        if not isinstance(query, str) or not query.strip():
            return jsonify({"msg": "Query must be a non-empty string"}), 400

        if not isinstance(role, str) or not role.strip():
            return jsonify({"msg": "Role must be a non-empty string"}), 400

        role = role.strip().lower()

        user_name = get_logged_in_user_name()
        if not user_name:
            return jsonify({"msg": "User not found"}), 404

        response_text = generate_response(query, role, user_name)

        return jsonify({"response": response_text}), 200
    except Exception as e:
        print(f"❌ Exception: {str(e)}")  # Log the error
        return jsonify({"msg": f"Error processing request: {str(e)}"}), 500

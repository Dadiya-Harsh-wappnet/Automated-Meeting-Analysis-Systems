from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from chatbot_llm import generate_response
from models import ChatHistory, User, SessionLocal
from db_tool import get_latest_active_session

chatbot_bp = Blueprint("chatbot_bp", __name__)

@chatbot_bp.route("/", methods=["POST"])
@jwt_required()
def chatbot_query():
    session = SessionLocal()
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"msg": "Invalid or missing JSON payload"}), 400
        
        role = data.get("role", "").strip().lower()
        query = data.get("query", "").strip()
        session_id = data.get("session_id")  # May be provided from the frontend

        user_id = get_jwt_identity()
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        user_name = f"{user.first_name} {user.last_name}"
        session_id = session_id or get_latest_active_session(user.id, session=session)
        response_text = generate_response(query, role, user_name, session_id)
        
        return jsonify({
            "response": response_text,
            "session_id": session_id
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"msg": f"Error processing request: {str(e)}"}), 500
    finally:
        session.close()

@chatbot_bp.route("/history/<int:user_id>", methods=["GET"])
@jwt_required()
def get_chat_history(user_id):
    session = SessionLocal()
    try:
        session_id = request.args.get("session_id")
        if not session_id:
            session_id = get_latest_active_session(user_id, session=session)
        chat_messages = (session.query(ChatHistory)
                         .filter_by(user_id=user_id, session_id=session_id)
                         .order_by(ChatHistory.created_at)
                         .all())
        history = [{"sender": msg.message_type, "text": msg.message} for msg in chat_messages]
        return jsonify({"history": history, "session_id": session_id}), 200
    except Exception as e:
        return jsonify({"msg": "Error retrieving chat history"}), 500
    finally:
        session.close()

# backend/routes/auth.py
from flask import Blueprint, request, jsonify
from models import Role, SessionLocal, User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

bcrypt = Bcrypt()
auth_bp = Blueprint("auth_bp", __name__)

# Registration Endpoint
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    role_name = data.get("role", "Employee")  # Default role is Employee

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    session = SessionLocal()
    try:
        # Fetch role_id from Role table
        role_obj = session.query(Role).filter_by(name=role_name).first()
        if not role_obj:
            return jsonify({"msg": "Invalid role"}), 400  # Role not found in DB
        
        if session.query(User).filter_by(email=email).first():
            return jsonify({"msg": "User already exists"}), 400

        new_user = User(
            email=email,
            password=password,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            first_name=first_name if first_name else "Unknown",
            last_name=last_name if last_name else "User",
            name=f"{first_name} {last_name}".strip(),
            role_id=role_obj.id
        )

        session.add(new_user)
        session.commit()
        return jsonify({"msg": "User registered successfully"}), 201
    finally:
        session.close()

# Login Endpoint (Now Returns Role)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({"msg": "Invalid credentials"}), 401

        token = create_access_token(identity=str(user.id))

        return jsonify({
            "token": token,
            "role": user.role.name  # ✅ Return role name instead of role_id
        }), 200
    finally:
        session.close()

# Protected Profile Endpoint
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    session = SessionLocal()
    try:
        user = session.query(User).get(current_user_id)
        if not user:
            return jsonify({"msg": "User not found"}), 404
        return jsonify({
            "id": user.id,
            "email": user.email,
            "role": user.role.name  # ✅ Ensure we return role name
        }), 200
    finally:
        session.close()

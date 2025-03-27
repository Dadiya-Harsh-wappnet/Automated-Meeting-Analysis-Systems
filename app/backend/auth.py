from flask import Blueprint, request, jsonify
from models import SessionLocal, User, Role, Department
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User Registration
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: payload
        schema:
          type: object
          required:
            - first_name
            - last_name
            - name
            - email
            - password
            - role
          properties:
            first_name:
              type: string
            last_name:
              type: string
            name:
              type: string
            email:
              type: string
            password:
              type: string
            role:
              type: string
            department:
              type: string
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing required fields or user already exists
      500:
        description: Registration failed
    """
    data = request.get_json()
    required_fields = ["first_name", "last_name", "name", "email", "password", "role"]
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing required fields"}), 400
    session = SessionLocal()
    try:
        if session.query(User).filter(User.email == data["email"]).first():
            return jsonify({"msg": "User with this email already exists"}), 400
        hashed_password = generate_password_hash(data["password"])
        role_record = session.query(Role).filter(Role.name.ilike(data["role"])).first()
        if not role_record:
            role_record = Role(name=data["role"])
            session.add(role_record)
            session.commit()
        department = None
        if "department" in data:
            department = session.query(Department).filter(Department.name.ilike(data["department"])).first()
            if not department:
                department = Department(name=data["department"])
                session.add(department)
                session.commit()
        new_user = User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            name=data["name"],
            email=data["email"],
            password_hash=hashed_password,
            password=data["password"],
            role_id=role_record.id,
            department_id=department.id if department else None
        )
        session.add(new_user)
        session.commit()
        return jsonify({"msg": "User registered successfully"}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"msg": "Registration failed", "error": str(e)}), 500
    finally:
        session.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: payload
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful, returns JWT token and user data.
      400:
        description: Email and password required.
      401:
        description: Invalid credentials.
      500:
        description: Login failed.
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"msg": "Email and password required"}), 400
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"msg": "Invalid credentials"}), 401
        access_token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(hours=1))
        return jsonify({
            "access_token": access_token, 
            "user": {
                "id": user.id, 
                "name": user.name, 
                "email": user.email, 
                "role": user.role.name
            }
        }), 200
    except Exception as e:
        return jsonify({"msg": "Login failed", "error": str(e)}), 500
    finally:
        session.close()

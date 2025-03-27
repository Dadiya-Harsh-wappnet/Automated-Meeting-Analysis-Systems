import logging
from flask import Flask, request
from flask_cors import CORS
from config import Config
from models import Base  # Now using our declarative Base
from sqlalchemy import create_engine
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

# Import our route blueprints
from routes.auth import auth_bp 
from routes.meetings import meetings_bp
from routes.chatbot import chatbot_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Create database engine and tables using our Base
engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
with app.app_context():
    Base.metadata.create_all(engine)

@app.before_request
def log_request_info():
    print("🔍 Incoming Request:")
    print(f"📌 Method: {request.method}")
    print(f"📌 Path: {request.path}")
    print(f"📌 Headers: {request.headers}")
    print(f"📌 Raw Body: {request.data}")  # ✅ This should show the request body


# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(meetings_bp, url_prefix="/api/meetings")
app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")

if __name__ == '__main__':
    app.run(debug=True)

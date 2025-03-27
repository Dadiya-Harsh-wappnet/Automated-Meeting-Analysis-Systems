import logging
from flask import Flask, request
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config
from database import init_db

# Import Blueprints
from routes.auth import auth_bp
from routes.meetings import meetings_bp
from routes.chatbot import chatbot_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
Bcrypt(app)
JWTManager(app)

init_db(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(meetings_bp, url_prefix="/api/meetings")
app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")

if __name__ == '__main__':
    app.run(debug=True)

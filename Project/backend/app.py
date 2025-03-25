# backend/app.py
from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

# Import our route blueprints
from routes.auth import auth_bp 
from routes.meetings import meetings_bp
from routes.chatbot import chatbot_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)  # Initialize Migrate


# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(meetings_bp, url_prefix="/api/meetings")
app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")

# Create database tables (use Flask-Migrate for production)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

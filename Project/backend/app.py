from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes import api

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Enable CORS for frontend

db.init_app(app)

# Register blueprints
app.register_blueprint(api)

# Create database tables (for development only; use migrations for production)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

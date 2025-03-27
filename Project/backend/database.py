from sqlalchemy import create_engine
from models import Base, SessionLocal
from config import Config

def init_db(app):
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=False)
    Base.metadata.create_all(engine)
    app.config["SQLALCHEMY_ENGINE"] = engine
    app.config["SQLALCHEMY_SESSION_LOCAL"] = SessionLocal

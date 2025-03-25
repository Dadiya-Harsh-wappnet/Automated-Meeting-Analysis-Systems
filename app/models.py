# models.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

Base = declarative_base()

def get_session(database_url=None):
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

# Users table: includes id, name, email, role, department, created_at.
class UserInfo(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False)   # Allowed values: 'HR', 'Employee', or 'Manager'
    department = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

# User performance table.
class UserPerformance(Base):
    __tablename__ = 'user_performance'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    performance_score = Column(Float, nullable=False)
    performance_date = Column(DateTime, default=datetime.utcnow)
    user = relationship("UserInfo", backref="performances")

# Meetings table.
class LearningMeeting(Base):
    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    scheduled_at = Column(DateTime, nullable=False)
    created_by = Column(Integer)  # References user id if applicable
    created_at = Column(DateTime, default=datetime.utcnow)

# Meeting participants table.
class MeetingParticipant(Base):
    __tablename__ = 'meeting_participants'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

# Meeting transcripts table: does not store user_id; uses speaker_label.
class LearningTranscript(Base):
    __tablename__ = 'meeting_transcripts'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    speaker_label = Column(String(50), nullable=False)  # e.g., "Employee - Alice Johnson"
    transcript = Column(Text, nullable=False)
    start_time = Column(Float)   # Seconds into the meeting
    end_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Skills table.
class Skills(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    skill_name = Column(String(255), unique=True, nullable=False)

# User skill recommendations table.
class UserSkillRecommendation(Base):
    __tablename__ = 'user_skill_recommendations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
    recommendation_date = Column(DateTime, default=datetime.utcnow)

# Chat history table (optional).
class ChatHistory(Base):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message_type = Column(String(10), nullable=False)  # 'user' or 'bot'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

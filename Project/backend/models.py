import os
from sqlalchemy import (create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Numeric)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, scoped_session
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # Change this if needed

# Create Engine
engine = create_engine(DATABASE_URL, echo=False)

# Create Session Factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base Class
Base = declarative_base()

# Create Tables
Base.metadata.create_all(engine)

# ----- Role -----
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

# ----- Department -----
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

# ----- User -----
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", backref="users")
    department = relationship("Department", backref="users")
    manager = relationship("User", remote_side=[id], backref="subordinates")

# ----- Meeting -----
class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    scheduled_start = Column(DateTime)
    scheduled_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    google_meet_link = Column(String(300))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", backref="created_meetings")

# ----- Meeting Participants -----
class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(50))  # "Host", "Attendee"
    joined_at = Column(DateTime)
    left_at = Column(DateTime)

# ----- Transcript -----
class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    transcript_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", backref="transcript")

# ----- Transcript Line -----
class TranscriptLine(Base):
    __tablename__ = "transcript_lines"
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("users.id"))
    speaker_label = Column(String(50))  # "Employee - Alice Johnson"
    start_time = Column(Float)  # Seconds into the meeting
    end_time = Column(Float)
    text = Column(Text, nullable=False)
    sentiment_score = Column(Numeric(3, 2))  # AI-based sentiment score
    created_at = Column(DateTime, default=datetime.utcnow)

    transcript = relationship("Transcript", backref="lines")
    speaker = relationship("User", backref="transcript_lines")

# ----- Performance Metric -----
class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    metric_type = Column(String(50), nullable=False)  # "Engagement", "Speaking Time"
    metric_value = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="performance_metrics")
    meeting = relationship("Meeting", backref="performance_metrics")

# ----- Task (Action Items) -----
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    assigned_to = Column(Integer, ForeignKey("users.id"))
    description = Column(Text, nullable=False)
    status = Column(String(50), default="Open")  # Open, In Progress, Completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting = relationship("Meeting", backref="tasks")
    assignee = relationship("User", backref="tasks")

# ----- Skills -----
class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    skill_name = Column(String(255), unique=True, nullable=False)

# ----- User Skill Recommendation -----
class UserSkillRecommendation(Base):
    __tablename__ = "user_skill_recommendations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    recommendation_date = Column(DateTime, default=datetime.utcnow)

# ----- Chat History -----
class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message_type = Column(String(10), nullable=False)  # "user" or "bot"
    session_id = Column(String(36))   # New column: conversation session identifier
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

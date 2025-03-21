# models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

# Users table
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # In your schema, this is of type user_role
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meetings_created = relationship("Meeting", back_populates="creator")
    meeting_participations = relationship("MeetingParticipant", back_populates="user")

# Meetings table
class Meeting(Base):
    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    scheduled_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("User", back_populates="meetings_created")
    participants = relationship("MeetingParticipant", back_populates="meeting")
    transcripts = relationship("MeetingTranscript", back_populates="meeting")

# Meeting Participants table
class MeetingParticipant(Base):
    __tablename__ = 'meeting_participants'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", back_populates="meeting_participations")

# Meeting Transcripts table
class MeetingTranscript(Base):
    __tablename__ = 'meeting_transcripts'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'))
    speaker_label = Column(String(50), nullable=False)
    transcript = Column(Text, nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="transcripts")

def get_engine(db_url):
    return create_engine(db_url)

def get_session(db_url):
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

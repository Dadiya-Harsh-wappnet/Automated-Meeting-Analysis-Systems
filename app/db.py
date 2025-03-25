# db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, desc
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
from dotenv import load_dotenv

from models import UserInfo, get_session  # Updated import: remove "app."
load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://your_db_user:your_db_password@localhost/your_db_name")
Base = declarative_base()

class Transcript(Base):
    __tablename__ = 'transcripts'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(String(50), nullable=True)
    speaker_label = Column(String(100))
    transcript = Column(Text)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def insert_transcript_lines_sqlalchemy(db_url=DB_URL, transcript_lines=[]):
    from models import get_session  # Import directly from models, not via app.models
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)  # Create table if it doesn't exist.
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        for line in transcript_lines:
            transcript_entry = Transcript(
                meeting_id=line.get('meeting_id'),
                speaker_label=line.get('speaker_label'),
                transcript=line.get('transcript'),
                start_time=line.get('start_time'),
                end_time=line.get('end_time')
            )
            session.add(transcript_entry)
        session.commit()
        print("Transcript lines inserted successfully using SQLAlchemy!")
    except Exception as e:
        session.rollback()
        print(f"Error inserting transcript lines: {e}")
    finally:
        session.close()

def get_recent_meeting_transcripts(meeting_id: int, limit: int = 3) -> str:
    from models import get_session
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    records = session.query(Transcript).filter(Transcript.meeting_id == str(meeting_id))\
                 .order_by(desc(Transcript.created_at)).limit(limit).all()
    session.close()
    if records:
        excerpts = " | ".join([t.transcript[:50] for t in records])
        return f"Recent Transcript Excerpts: {excerpts}"
    else:
        return "No transcript data available for this meeting."
    
def get_personal_data(user_id):
    """
    Retrieve and return basic personal data for the given user.
    Uses the UserInfo table to fetch name, email, role, and department.
    """
    session = get_session()
    user = session.query(UserInfo).filter(UserInfo.id == user_id).first()
    session.close()
    if user:
        return f"Name: {user.name}, Email: {user.email}, Role: {user.role}, Department: {user.department}"
    else:
        return f"No personal data found for user ID {user_id}."

def get_team_data(manager_id):
    """
    Retrieve team data for a manager.
    For simplicity, this implementation assumes that employees in the same department as the manager
    belong to their team. Adjust the logic as needed.
    """
    session = get_session()
    manager = session.query(UserInfo).filter(UserInfo.id == manager_id).first()
    if not manager:
        session.close()
        return f"No record found for manager with ID {manager_id}."
    
    team_members = session.query(UserInfo)\
        .filter(UserInfo.department == manager.department, UserInfo.id != manager_id)\
        .all()
    session.close()
    
    if team_members:
        members_list = ", ".join([f"{member.name} ({member.role})" for member in team_members])
        return f"Team for manager {manager.name} (Department: {manager.department}): {members_list}"
    else:
        return f"No team data available for manager {manager.name}."

def get_all_employee_data():
    """
    Retrieve and return data for all employees.
    This function fetches all users and returns a formatted string.
    """
    session = get_session()
    employees = session.query(UserInfo).all()
    session.close()
    
    if employees:
        employee_list = "\n".join([f"ID: {emp.id}, Name: {emp.name}, Role: {emp.role}, Department: {emp.department}" for emp in employees])
        return f"All Employee Data:\n{employee_list}"
    else:
        return "No employee data available."

#backend/db_tool.py
import logging
import uuid
import re
import traceback
from datetime import datetime, timedelta
from requests import Session
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from functools import wraps

from models import (SessionLocal, User as UserInfo, 
                    PerformanceMetric as UserPerformance, 
                    Transcript as LearningTranscript, 
                    MeetingParticipant, 
                    UserSkillRecommendation, 
                    Skill as Skills, 
                    ChatHistory)

# Configure logging
logging.basicConfig(filename="db_tool.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ------------------- Helper: Session Decorator -------------------
def with_session(func):
    """
    Decorator to handle session creation, commit, and closing.
    If a session is passed in kwargs, it uses that instead.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_provided = kwargs.get("session") is not None
        session = kwargs.get("session", SessionLocal())
        try:
            kwargs["session"] = session
            result = func(*args, **kwargs)
            if not session_provided:
                session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Error in {func.__name__}: {e}\n{traceback.format_exc()}")
            raise
        finally:
            if not session_provided:
                session.close()
    return wrapper

# ------------------- User and Data Retrieval -------------------
@with_session
def get_user_id_by_name(user_name: str, session=None) -> str:
    """
    Retrieve the user ID for the given user name using case-insensitive partial matching.
    """
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    return str(user.id) if user else None

@with_session
def get_employee_performance_by_name(user_name: str, session=None) -> str:
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    if user:
        performances = session.query(UserPerformance).filter(UserPerformance.user_id == user.id).all()
        if performances:
            details = "\n".join([f"Score: {p.performance_score}, Date: {p.created_at}" for p in performances])
            return f"Performance records for {user.name}:\n{details}"
        else:
            return f"No performance records found for {user.name}."
    else:
        return f"No record found for employee '{user_name}'."

@with_session
def get_recent_meeting_transcripts(meeting_id: int, limit: int = 3, session=None) -> str:
    transcripts = session.query(LearningTranscript)\
                    .filter(LearningTranscript.meeting_id == meeting_id)\
                    .order_by(desc(LearningTranscript.created_at)).limit(limit).all()
    if transcripts:
        excerpts = " | ".join([t.transcript_text[:50] for t in transcripts])
        return f"Recent Transcript Excerpts: {excerpts}"
    else:
        return "No transcript data available for this meeting."

@with_session
def get_department_roster(department: str, session=None) -> str:
    department = department.strip()
    # Assuming department is stored as a string in UserInfo.department
    users = session.query(UserInfo).filter(UserInfo.department.ilike(f'%{department}%')).all()
    if users:
        roster = " | ".join([f"{u.name} ({u.role})" for u in users])
        return f"Department Roster for {department}: {roster}"
    else:
        return f"No employees found in department '{department}'."

@with_session
def get_meeting_participants(meeting_id: int, session=None) -> str:
    participants = session.query(MeetingParticipant).filter(MeetingParticipant.meeting_id == meeting_id).all()
    if participants:
        names = []
        for part in participants:
            user = session.query(UserInfo).filter(UserInfo.id == part.user_id).first()
            if user:
                names.append(user.name)
        return f"Participants in meeting {meeting_id}: " + ", ".join(names)
    else:
        return f"No participants found for meeting ID {meeting_id}."

@with_session
def get_skill_recommendations_by_name(user_name: str, session=None) -> str:
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    if not user:
        return f"No record found for employee '{user_name}'."
    # Use join to fetch recommended skills in one query
    recommendations = (session.query(Skills.skill_name)
                          .join(UserSkillRecommendation, UserSkillRecommendation.skill_id == Skills.id)
                          .filter(UserSkillRecommendation.user_id == user.id)
                          .all())
    if recommendations:
        skill_names = [r[0] for r in recommendations]
        return f"Recommended skills for {user.name}: " + ", ".join(skill_names)
    else:
        return f"No skill recommendations found for {user.name}."

@with_session
def store_transcript(data: dict, session=None) -> None:
    meeting_id = data.get("meeting_id")
    transcripts = data.get("transcripts", [])
    for seg in transcripts:
        record = LearningTranscript(
            meeting_id=meeting_id,
            speaker_label=seg.get("speaker", "Unknown"),
            transcript_text=seg.get("transcript", "")
        )
        session.add(record)
    # Commit happens in the decorator

@with_session
def get_personal_data(user_id: int, session=None) -> dict:
    user = session.query(UserInfo).filter_by(id=user_id).first()
    if not user:
        return {"error": "User not found."}
    performance = session.query(UserPerformance)\
                         .filter_by(user_id=user_id)\
                         .order_by(UserPerformance.created_at.desc()).first()
    return {
        "Name": user.name,
        "Email": user.email,
        "Role": user.role,
        "Department": user.department,
        "Latest Performance Score": performance.performance_score if performance else "No data available"
    }

@with_session
def get_recent_meeting_transcripts_by_meeting(meeting_id: int, session=None) -> list:
    transcripts = session.query(LearningTranscript).filter_by(meeting_id=meeting_id).all()
    if not transcripts:
        return []
    return [{"Speaker": t.transcript_text[:50], "Transcript": t.transcript_text} for t in transcripts]

@with_session
def get_team_data(manager_id: int, session=None) -> list:
    employees = session.query(UserInfo).filter_by(role="Employee").all()
    if not employees:
        return []
    team_data = []
    for employee in employees:
        performance = session.query(UserPerformance)\
                             .filter_by(user_id=employee.id)\
                             .order_by(UserPerformance.created_at.desc()).first()
        team_data.append({
            "Employee Name": employee.name,
            "Email": employee.email,
            "Department": employee.department,
            "Latest Performance Score": performance.performance_score if performance else "No data available"
        })
    return team_data

@with_session
def get_all_employee_data(session=None) -> list:
    employees = session.query(UserInfo).filter_by(role="Employee").all()
    if not employees:
        return []
    response = []
    for emp in employees:
        performance = session.query(UserPerformance)\
                             .filter_by(user_id=emp.id)\
                             .order_by(UserPerformance.created_at.desc()).first()
        response.append({
            "Name": emp.name,
            "Email": emp.email,
            "Department": emp.department,
            "Latest Performance Score": performance.metric_value if performance else "No data available"
        })
    return response

# ------------------- Chat Session Management -------------------
@with_session
def get_latest_active_session(user_id: int, inactivity_threshold=30, session: Session = None) -> str:
    """
    Get the latest active session for a user based on an inactivity threshold (in minutes).
    If no active session exists, return a new session ID.
    """
    time_threshold = datetime.utcnow() - timedelta(minutes=inactivity_threshold)
    latest_chat = (
        session.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .first()
    )

    if latest_chat and latest_chat.created_at > time_threshold:
        return latest_chat.session_id
    
    # No active session found, create a new one and store it.
    new_session_id = str(uuid.uuid4())
    return new_session_id  # Just return the new session ID instead of creating an entry here


@with_session
def store_chat_history(user_id: int, message: str, message_type: str = "user", session_id: str = None, session=None) -> str:
    """
    Store chatbot conversation history. If session_id is not provided, fetch or create one.
    """
    if not session_id:
        session_id = get_latest_active_session(user_id, session=session) or str(uuid.uuid4())
    
    chat_entry = ChatHistory(user_id=user_id, message=message, message_type=message_type, session_id=session_id)
    session.add(chat_entry)

    return session_id  # Ensure we return the session_id

@with_session
def get_chat_history_for_user(user_id: int, session_id: str = None, limit: int = 10, session=None) -> list:
    """
    Retrieve the last 'limit' chat messages for a user. If session_id is None, fetch the latest active session.
    """
    if not session_id:
        session_id = get_latest_active_session(user_id, session=session)
    if not session_id:
        return []  # No active session found
    history = (session.query(ChatHistory)
               .filter(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id)
               .order_by(ChatHistory.created_at.asc())
               .limit(limit)
               .all())
    return [{"type": entry.message_type, "message": entry.message, "session_id": entry.session_id} for entry in history]

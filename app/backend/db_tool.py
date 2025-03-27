import logging
import uuid
import re
import traceback
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from models import (
    SessionLocal,
    User as UserInfo,
    PerformanceMetric as UserPerformance,
    Transcript as LearningTranscript,
    TranscriptLine,
    MeetingParticipant,
    UserSkillRecommendation,
    Skill as Skills,
    ChatHistory,
    Meeting,
    Task,
)
from task_extraction import extract_tasks_from_text  # Import the LLM extraction helper

# Configure logging
logging.basicConfig(
    filename="db_tool.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def with_session(func: Callable) -> Callable:
    """
    Decorator to handle session creation, commit, and closing.
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
            logger.error("Error in %s: %s\n%s", func.__name__, e, traceback.format_exc())
            raise
        finally:
            if not session_provided:
                session.close()
    return wrapper

def compute_fingerprint(description: str) -> str:
    """
    Compute a SHA-256 hash for a given description.
    """
    return hashlib.sha256(description.encode('utf-8')).hexdigest()

# ------------------- User and Data Retrieval Tools -------------------

@with_session
def get_user_id_by_name(user_name: str, session: Optional[Any] = None) -> Optional[str]:
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    return str(user.id) if user else None

@with_session
def get_employee_performance_by_name(user_name: str, session: Optional[Any] = None) -> str:
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    if user:
        performances = session.query(UserPerformance).filter(UserPerformance.user_id == user.id).all()
        if performances:
            details = "\n".join([f"Score: {p.performance_score}, Date: {p.created_at}" for p in performances])
            return f"Performance records for {user.name}:\n{details}"
        return f"No performance records found for {user.name}."
    return f"No record found for employee '{user_name}'."

@with_session
def get_recent_meeting_transcripts(meeting_id: int, limit: int = 3, session: Optional[Any] = None) -> str:
    transcripts = (
        session.query(LearningTranscript)
        .filter(LearningTranscript.meeting_id == meeting_id)
        .order_by(desc(LearningTranscript.created_at))
        .limit(limit)
        .all()
    )
    if transcripts:
        excerpts = " | ".join([t.transcript_text[:50] for t in transcripts])
        return f"Recent Transcript Excerpts: {excerpts}"
    return "No transcript data available for this meeting."

@with_session
def get_department_roster(department: str, session: Optional[Any] = None) -> str:
    department = department.strip()
    users = session.query(UserInfo).filter(UserInfo.department.ilike(f'%{department}%')).all()
    if users:
        roster = " | ".join([f"{u.name} ({u.role})" for u in users])
        return f"Department Roster for {department}: {roster}"
    return f"No employees found in department '{department}'."

@with_session
def get_meeting_participants(meeting_id: int, session: Optional[Any] = None) -> str:
    participants = session.query(MeetingParticipant).filter(MeetingParticipant.meeting_id == meeting_id).all()
    if participants:
        names = []
        for part in participants:
            user = session.query(UserInfo).filter(UserInfo.id == part.user_id).first()
            if user:
                names.append(user.name)
        return f"Participants in meeting {meeting_id}: " + ", ".join(names)
    return f"No participants found for meeting ID {meeting_id}."

@with_session
def get_skill_recommendations_by_name(user_name: str, session: Optional[Any] = None) -> str:
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    if not user:
        return f"No record found for employee '{user_name}'."
    recommendations = (
        session.query(Skills.skill_name)
        .join(UserSkillRecommendation, UserSkillRecommendation.skill_id == Skills.id)
        .filter(UserSkillRecommendation.user_id == user.id)
        .all()
    )
    if recommendations:
        skill_names = [r[0] for r in recommendations]
        return f"Recommended skills for {user.name}: " + ", ".join(skill_names)
    return f"No skill recommendations found for {user.name}."

@with_session
def get_personal_data(user_id: int, session: Optional[Any] = None) -> Dict[str, Union[str, Any]]:
    user = session.query(UserInfo).filter_by(id=user_id).first()
    if not user:
        return {"error": "User not found."}
    performance = session.query(UserPerformance).filter_by(user_id=user_id).order_by(UserPerformance.created_at.desc()).first()
    return {
        "Name": user.name,
        "Email": user.email,
        "Role": user.role,
        "Department": user.department,
        "Latest Performance Score": performance.performance_score if performance else "No data available",
    }

@with_session
def get_recent_meeting_transcripts_by_meeting(meeting_id: int, session: Optional[Any] = None) -> List[Dict[str, str]]:
    transcripts = session.query(LearningTranscript).filter_by(meeting_id=meeting_id).all()
    if not transcripts:
        return []
    return [{"Speaker": t.transcript_text[:50], "Transcript": t.transcript_text} for t in transcripts]

@with_session
def get_team_data(manager_id: int, session: Optional[Any] = None) -> List[Dict[str, Union[str, Any]]]:
    employees = session.query(UserInfo).filter_by(role="Employee").all()
    if not employees:
        return []
    team_data = []
    for employee in employees:
        performance = session.query(UserPerformance).filter_by(user_id=employee.id).order_by(UserPerformance.created_at.desc()).first()
        team_data.append({
            "Employee Name": employee.name,
            "Email": employee.email,
            "Department": employee.department,
            "Latest Performance Score": performance.performance_score if performance else "No data available",
        })
    return team_data

@with_session
def get_all_employee_data(session: Optional[Any] = None) -> List[Dict[str, Union[str, Any]]]:
    employees = session.query(UserInfo).filter_by(role="Employee").all()
    if not employees:
        return []
    response = []
    for emp in employees:
        performance = session.query(UserPerformance).filter_by(user_id=emp.id).order_by(UserPerformance.created_at.desc()).first()
        response.append({
            "Name": emp.name,
            "Email": emp.email,
            "Department": emp.department,
            "Latest Performance Score": performance.metric_value if performance else "No data available",
        })
    return response

# ------------------- Task Management Tools -------------------

@with_session
def get_tasks_by_meeting(meeting_id: int, session: Optional[Any] = None) -> List[Dict[str, Union[str, Any]]]:
    tasks = session.query(Task).filter(Task.meeting_id == meeting_id).all()
    result = []
    for task in tasks:
        result.append({
            "Task ID": task.id,
            "Assigned To": task.assigned_to,
            "Description": task.description,
            "Status": task.status,
            "Created At": task.created_at,
            "Updated At": task.updated_at,
        })
    return result

@with_session
def create_task(meeting_id: int, assigned_to: Optional[int], description: str, status: str = "Open", session: Optional[Any] = None) -> None:
    fp = compute_fingerprint(description)
    task = Task(
        meeting_id=meeting_id,
        assigned_to=assigned_to,
        description=description,
        status=status,
        fingerprint=fp,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(task)

@with_session
def update_task_status(task_id: int, status: str, session: Optional[Any] = None) -> None:
    task = session.query(Task).filter_by(id=task_id).first()
    if task:
        task.status = status
        task.updated_at = datetime.utcnow()
    else:
        logger.warning("Task with ID %s not found.", task_id)

# ------------------- Performance Metric Tools -------------------

@with_session
def store_performance_metric(user_id: int, metric_type: str, metric_value: float, meeting_id: Optional[int] = None, session: Optional[Any] = None) -> None:
    performance = UserPerformance(
        user_id=user_id,
        meeting_id=meeting_id,
        metric_type=metric_type,
        metric_value=metric_value,
        created_at=datetime.utcnow(),
    )
    session.add(performance)

# ------------------- Meeting Tools -------------------

@with_session
def get_meeting_details(meeting_id: int, session: Optional[Any] = None) -> Dict[str, Union[str, Any]]:
    meeting = session.query(Meeting).filter_by(id=meeting_id).first()
    if meeting:
        return {
            "Meeting ID": meeting.id,
            "Title": meeting.title,
            "Description": meeting.description,
            "Scheduled Start": meeting.scheduled_start,
            "Scheduled End": meeting.scheduled_end,
            "Actual Start": meeting.actual_start,
            "Actual End": meeting.actual_end,
            "Google Meet Link": meeting.google_meet_link,
            "Created By": meeting.created_by,
            "Created At": meeting.created_at,
        }
    return {"error": f"Meeting with ID {meeting_id} not found."}

# ------------------- Task Automation from Transcripts -------------------

@with_session
def auto_generate_tasks_from_transcript(meeting_id: int, session: Optional[Any] = None) -> List[Dict[str, Union[str, Any]]]:
    generated_tasks = []
    transcripts = session.query(LearningTranscript).filter(LearningTranscript.meeting_id == meeting_id).all()
    for transcript in transcripts:
        action_items = extract_tasks_from_text(transcript.transcript_text)
        for description in action_items:
            description = description.strip()
            if description:
                fp = compute_fingerprint(description)
                # Check if a task with the same fingerprint already exists
                existing = session.query(Task).filter(
                    Task.meeting_id == meeting_id,
                    Task.fingerprint == fp
                ).first()
                if existing:
                    continue
                task = Task(
                    meeting_id=meeting_id,
                    assigned_to=None,
                    description=description,
                    status="Open",
                    fingerprint=fp,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(task)
                generated_tasks.append({
                    "Task Description": description,
                    "Meeting ID": meeting_id,
                    "Status": "Open"
                })
    return generated_tasks

# ------------------- Chat Session Management Tools -------------------

@with_session
def get_latest_active_session(user_id: int, inactivity_threshold: int = 30, session: Optional[Any] = None) -> str:
    time_threshold = datetime.utcnow() - timedelta(minutes=inactivity_threshold)
    latest_chat = session.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.created_at.desc()).first()
    if latest_chat and latest_chat.created_at > time_threshold:
        return latest_chat.session_id
    return str(uuid.uuid4())

@with_session
def store_chat_history(user_id: int, message: str, message_type: str = "user", session_id: Optional[str] = None, session: Optional[Any] = None) -> str:
    if not session_id:
        session_id = get_latest_active_session(user_id, session=session) or str(uuid.uuid4())
    chat_entry = ChatHistory(
        user_id=user_id,
        message=message,
        message_type=message_type,
        session_id=session_id,
    )
    session.add(chat_entry)
    return session_id

@with_session
def get_chat_history_for_user(user_id: int, session_id: Optional[str] = None, limit: int = 10, session: Optional[Any] = None) -> List[Dict[str, str]]:
    if not session_id:
        session_id = get_latest_active_session(user_id, session=session)
    if not session_id:
        return []
    history = session.query(ChatHistory).filter(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id).order_by(ChatHistory.created_at.asc()).limit(limit).all()
    return [{"type": entry.message_type, "message": entry.message, "session_id": entry.session_id} for entry in history]

# # db_tool.py
# from models import get_session, UserInfo

# def get_user_id_by_name(user_name: str) -> str:
#     """
#     Retrieves the user ID for the given user name from the database.
#     Uses case-insensitive partial matching.
#     """
#     session = get_session()
#     user_name = user_name.strip()
#     user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
#     session.close()
#     if user:
#         return f"Employee ID for {user.name} is {user.id}."
#     else:
#         return f"No record found for employee '{user_name}'."

# db_tools.py
import logging
from sqlalchemy import desc
from models import get_session, UserInfo, UserPerformance, LearningTranscript, MeetingParticipant, UserSkillRecommendation, Skills

logger = logging.getLogger(__name__)

def get_user_id_by_name(user_name: str) -> str:
    """
    Retrieve the user ID for the given user name using case-insensitive partial matching.
    """
    session = get_session()
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    session.close()
    if user:
        return f"Employee ID for {user.name} is {user.id}."
    else:
        return f"No record found for employee '{user_name}'."

def get_employee_performance_by_name(user_name: str) -> str:
    """
    Retrieve detailed performance data for an employee given their name.
    Returns a summary of performance scores and dates.
    """
    session = get_session()
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    response = ""
    if user:
        performances = session.query(UserPerformance).filter(UserPerformance.user_id == user.id).all()
        if performances:
            details = "\n".join([f"Score: {p.performance_score}, Date: {p.performance_date}" for p in performances])
            response = f"Performance records for {user.name}:\n{details}"
        else:
            response = f"No performance records found for {user.name}."
    else:
        response = f"No record found for employee '{user_name}'."
    session.close()
    return response

def get_recent_meeting_transcripts(meeting_id: int, limit: int = 3) -> str:
    """
    Retrieve transcript excerpts for a specific meeting.
    """
    session = get_session()
    transcripts = session.query(LearningTranscript).filter(LearningTranscript.meeting_id == meeting_id)\
                  .order_by(desc(LearningTranscript.created_at)).limit(limit).all()
    session.close()
    if transcripts:
        excerpts = " | ".join([t.transcript[:50] for t in transcripts])
        return f"Recent Transcript Excerpts: {excerpts}"
    else:
        return "No transcript data available for this meeting."

def get_department_roster(department: str) -> str:
    """
    Retrieve a list of employees in a given department.
    """
    session = get_session()
    department = department.strip()
    users = session.query(UserInfo).filter(UserInfo.department.ilike(f'%{department}%')).all()
    session.close()
    if users:
        roster = " | ".join([f"{u.name} ({u.role})" for u in users])
        return f"Department Roster for {department}: {roster}"
    else:
        return f"No employees found in department '{department}'."

def get_meeting_participants(meeting_id: int) -> str:
    """
    Retrieve a list of names of all participants in a specific meeting.
    """
    from models import MeetingParticipant  # Imported here for clarity
    session = get_session()
    participants = session.query(MeetingParticipant).filter(MeetingParticipant.meeting_id == meeting_id).all()
    session.close()
    if participants:
        # For each participant, fetch the user record to get the name.
        names = []
        session = get_session()
        for part in participants:
            user = session.query(UserInfo).filter(UserInfo.id == part.user_id).first()
            if user:
                names.append(user.name)
        session.close()
        return f"Participants in meeting {meeting_id}: " + ", ".join(names)
    else:
        return f"No participants found for meeting ID {meeting_id}."

def get_skill_recommendations_by_name(user_name: str) -> str:
    """
    Retrieve recommended skills for an employee by their name.
    """
    session = get_session()
    user_name = user_name.strip()
    user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
    response = ""
    if user:
        recommendations = session.query(UserSkillRecommendation).filter(UserSkillRecommendation.user_id == user.id).all()
        if recommendations:
            # For each recommendation, get the skill name.
            skill_names = []
            for rec in recommendations:
                skill = session.query(Skills).filter(Skills.id == rec.skill_id).first()
                if skill:
                    skill_names.append(skill.skill_name)
            response = f"Recommended skills for {user.name}: " + ", ".join(skill_names)
        else:
            response = f"No skill recommendations found for {user.name}."
    else:
        response = f"No record found for employee '{user_name}'."
    session.close()
    return response


def store_transcript(data):
    """
    Save transcript data.
    Data format should be a dict:
      {
         "meeting_id": <int>,
         "transcripts": [
             {"speaker": "Speaker 1", "transcript": "Text", "start": 0.0, "end": 5.0},
             ...
         ]
      }
    """
    session = get_session()
    meeting_id = data.get("meeting_id")
    transcripts = data.get("transcripts", [])
    for seg in transcripts:
        record = LearningTranscript(
            meeting_id=meeting_id,
            speaker_label=seg.get("speaker", "Unknown"),
            transcript=seg.get("transcript", ""),
            start_time=seg.get("start", 0.0),
            end_time=seg.get("end", 0.0)
        )
        session.add(record)
    session.commit()
    session.close()

from sqlalchemy.orm import Session
from models import get_session, UserInfo, UserPerformance, LearningMeeting, LearningTranscript, MeetingParticipant, UserSkillRecommendation, Skills, ChatHistory

# Initialize DB session
session = get_session()

def get_personal_data(user_id):
    """Fetch personal details and performance data for a given user."""
    user = session.query(UserInfo).filter_by(id=user_id).first()
    if not user:
        return "User not found."
    
    performance = session.query(UserPerformance).filter_by(user_id=user_id).order_by(UserPerformance.performance_date.desc()).first()
    
    response = {
        "Name": user.name,
        "Email": user.email,
        "Role": user.role,
        "Department": user.department,
        "Latest Performance Score": performance.performance_score if performance else "No data available"
    }
    
    return response

def get_recent_meeting_transcripts(meeting_id):
    """Fetch transcripts of a given meeting."""
    transcripts = session.query(LearningTranscript).filter_by(meeting_id=meeting_id).all()
    if not transcripts:
        return "No transcripts found for this meeting."
    
    response = [{"Speaker": t.speaker_label, "Transcript": t.transcript} for t in transcripts]
    return response

def get_team_data(manager_id):
    """Fetch team members and their latest performance scores for a given manager."""
    employees = session.query(UserInfo).filter_by(role="Employee").all()
    
    if not employees:
        return "No team data available."

    team_data = []
    for employee in employees:
        performance = session.query(UserPerformance).filter_by(user_id=employee.id).order_by(UserPerformance.performance_date.desc()).first()
        team_data.append({
            "Employee Name": employee.name,
            "Email": employee.email,
            "Department": employee.department,
            "Latest Performance Score": performance.performance_score if performance else "No data available"
        })

    return team_data

def get_all_employee_data():
    """Fetch all employees' details (for HR)."""
    employees = session.query(UserInfo).filter_by(role="Employee").all()
    
    if not employees:
        return "No employee data found."
    
    response = []
    for emp in employees:
        performance = session.query(UserPerformance).filter_by(user_id=emp.id).order_by(UserPerformance.performance_date.desc()).first()
        response.append({
            "Name": emp.name,
            "Email": emp.email,
            "Department": emp.department,
            "Latest Performance Score": performance.performance_score if performance else "No data available"
        })
    
    return response

def store_chat_history(user_id, message, message_type="user"):
    """Store chatbot conversation history."""
    chat_entry = ChatHistory(user_id=user_id, message=message, message_type=message_type)
    session.add(chat_entry)
    session.commit()


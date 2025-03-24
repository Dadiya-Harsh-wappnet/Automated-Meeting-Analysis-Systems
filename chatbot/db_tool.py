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

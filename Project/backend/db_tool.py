import logging
from sqlalchemy import desc
from models import SessionLocal, User as UserInfo, PerformanceMetric as UserPerformance, Transcript as LearningTranscript, MeetingParticipant, UserSkillRecommendation, Skill as Skills, ChatHistory

logging.basicConfig(filename="db_tool.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_user_id_by_name(user_name: str, session=None) -> str:
    """
    Retrieve the user ID for the given user name using case-insensitive partial matching.
    If a session is provided, it will be used; otherwise, a new one is created.
    """
    own_session = False
    if session is None:
        session = SessionLocal()
        own_session = True
    try:
        user_name = user_name.strip()
        user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
        return str(user.id) if user else None
    finally:
        if own_session:
            session.close()

def get_employee_performance_by_name(user_name: str) -> str:
    """
    Retrieve detailed performance data for an employee given their name.
    Returns a summary of performance scores and dates.
    """
    session = SessionLocal()
    try:    
        user_name = user_name.strip()
        user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
        
        response = ""
        if user:
            performances = session.query(UserPerformance).filter(UserPerformance.user_id == user.id).all()
            if performances:
                details = "\n".join([f"Score: {p.performance_score}, Date: {p.created_at}" for p in performances])
                response = f"Performance records for {user.name}:\n{details}"
            else:
                response = f"No performance records found for {user.name}."
        else:
            response = f"No record found for employee '{user_name}'."
        return response
    finally:
        session.close()

def get_recent_meeting_transcripts(meeting_id: int, limit: int = 3) -> str:
    """
    Retrieve transcript excerpts for a specific meeting.
    """
    session = SessionLocal()
    try:
        transcripts = session.query(LearningTranscript).filter(LearningTranscript.meeting_id == meeting_id)\
                    .order_by(desc(LearningTranscript.created_at)).limit(limit).all()
        if transcripts:
            excerpts = " | ".join([t.transcript_text[:50] for t in transcripts])
            return f"Recent Transcript Excerpts: {excerpts}"
        else:
            return "No transcript data available for this meeting."
    finally:
        session.close()

def get_department_roster(department: str) -> str:
    """
    Retrieve a list of employees in a given department.
    """
    session = SessionLocal()
    try:
        department = department.strip()
        users = session.query(UserInfo).filter(UserInfo.department.ilike(f'%{department}%')).all()
        if users:
            roster = " | ".join([f"{u.name} ({u.role})" for u in users])
            return f"Department Roster for {department}: {roster}"
        else:
            return f"No employees found in department '{department}'."
    finally:
        session.close()

def get_meeting_participants(meeting_id: int) -> str:
    """
    Retrieve a list of names of all participants in a specific meeting.
    """
    from models import MeetingParticipant  # Imported here for clarity
    session = SessionLocal()
    try:
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
    finally:
        session.close()

def get_skill_recommendations_by_name(user_name: str) -> str:
    """
    Retrieve recommended skills for an employee by their name.
    """
    session = SessionLocal()
    try:
        user_name = user_name.strip()
        user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_name}%')).first()
        response = ""
        if user:
            recommendations = session.query(UserSkillRecommendation).filter(UserSkillRecommendation.user_id == user.id).all()
            if recommendations:
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
    finally:
        session.close()
    return response

def store_transcript(data: dict) -> None:
    """
    Save transcript data.
    Data format should be a dict:
      {
         'meeting_id': <int>,
         'transcripts': [
             {'speaker': 'Speaker 1', 'transcript': 'Text', 'start': 0.0, 'end': 5.0},
             ...
         ]
      }
    """
    session = SessionLocal()
    try:
        meeting_id = data.get("meeting_id")
        transcripts = data.get("transcripts", [])
        for seg in transcripts:
            record = LearningTranscript(
                meeting_id=meeting_id,
                speaker_label=seg.get("speaker", "Unknown"),
                transcript_text=seg.get("transcript", "")
                # Adjust start_time/end_time if needed
            )
            session.add(record)
        session.commit()
    finally:
        session.close()

def get_personal_data(user_id: int) -> dict:
    """Fetch personal details and performance data for a given user."""
    session = SessionLocal()
    try:
        user = session.query(UserInfo).filter_by(id=user_id).first()
        if not user:
            return {"error": "User not found."}
        performance = session.query(UserPerformance).filter_by(user_id=user_id).order_by(UserPerformance.created_at.desc()).first()
        response = {
            "Name": user.name,
            "Email": user.email,
            "Role": user.role,
            "Department": user.department,
            "Latest Performance Score": performance.performance_score if performance else "No data available"
        }
    finally:
        session.close()
    return response

def get_recent_meeting_transcripts_by_meeting(meeting_id: int) -> list:
    """Fetch transcripts of a given meeting."""
    session = SessionLocal()
    try:
        transcripts = session.query(LearningTranscript).filter_by(meeting_id=meeting_id).all()
        if not transcripts:
            return []
        response = [{"Speaker": t.transcript_text[:50], "Transcript": t.transcript_text} for t in transcripts]
    finally:
        session.close()
    return response

def get_team_data(manager_id: int) -> list:
    """Fetch team members and their latest performance scores for a given manager."""
    session = SessionLocal()
    try:
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
                "Latest Performance Score": performance.performance_score if performance else "No data available"
            })
    finally:
        session.close()
    return team_data

def get_all_employee_data() -> list:
    """Fetch all employees' details (for HR)."""
    session = SessionLocal()
    try:
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
                "Latest Performance Score": performance.performance_score if performance else "No data available"
            })
    finally:
        session.close()
    return response

def store_chat_history(user_id: int, message: str, message_type: str = "user") -> None:
    """
    Store chatbot conversation history using the existing ChatHistory table.
    """
    session = SessionLocal()
    try:
        chat_entry = ChatHistory(user_id=user_id, message=message, message_type=message_type)
        session.add(chat_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error storing chat history: {e}")
    finally:
        session.close()

def get_chat_history_for_user(user_id: int, limit: int = 10) -> list:
    """
    Retrieve the last 'limit' chat messages for a user.
    """
    session = SessionLocal()
    try:
        history = session.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.created_at.desc()).limit(limit).all()
        history.reverse()  # Oldest first
        return [f"{entry.message_type}: {entry.message}" for entry in history]
    finally:
        session.close()

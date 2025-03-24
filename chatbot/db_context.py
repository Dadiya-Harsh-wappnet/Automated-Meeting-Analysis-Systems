# db_context.py
import logging
from sqlalchemy import desc
from models import get_session, UserInfo, LearningTranscript, UserPerformance
from db_tool import get_employee_performance_by_name  # Reuse tool for detailed performance

logger = logging.getLogger(__name__)

def retrieve_db_context(role: str, user_identifier: str = None) -> str:
    """
    Retrieve context from the database based on the user's role and name.
    
    For employees (or if HR specifies an employee name):
      - Fetch the user's basic profile (including email, department, role).
      - Append detailed performance records using the tool from db_tools.py.
      - Retrieve recent transcript excerpts.
    
    For managers:
      - Retrieve recent meeting transcript excerpts.
    
    For HR without a specified employee name:
      - Return the overall employee roster and overall average performance score.
    """
    session = get_session()
    info = ""
    
    if (role.lower() == "employee" or (role.lower() == "hr" and user_identifier)) and user_identifier:
        user_identifier = user_identifier.strip()
        # Retrieve the user record.
        user = session.query(UserInfo).filter(UserInfo.name.ilike(f'%{user_identifier}%')).first()
        if user:
            logger.info(f"Found user: {user.name}")
            info += (f"Employee Profile: {user.name}, Email: {user.email}, "
                     f"Department: {user.department}, Role: {user.role}.\n")
            # Delegate performance details to the DB tool.
            performance_details = get_employee_performance_by_name(user_identifier)
            info += performance_details + "\n"
            # Retrieve recent transcript excerpts.
            transcripts = session.query(LearningTranscript).filter(
                LearningTranscript.speaker_label.ilike(f"%{user.name}%")
            ).order_by(desc(LearningTranscript.created_at)).limit(3).all()
            if transcripts:
                excerpts = " | ".join([t.transcript[:50] for t in transcripts])
                info += f"Recent Transcript Excerpts: {excerpts}.\n"
            else:
                info += "No transcript excerpts found for this employee.\n"
        else:
            info += f"No record found for employee '{user_identifier}'.\n"
    elif role.lower() == "manager":
        transcripts = session.query(LearningTranscript).order_by(desc(LearningTranscript.created_at)).limit(3).all()
        if transcripts:
            excerpts = " | ".join([t.transcript[:50] for t in transcripts])
            info += f"Recent Meeting Transcript Excerpts: {excerpts}.\n"
        else:
            info += "No recent transcripts available.\n"
    elif role.lower() == "hr" and not user_identifier:
        users = session.query(UserInfo).all()
        if users:
            roster = " | ".join([f"{u.name} ({u.role})" for u in users])
            info += f"Employee Roster: {roster}.\n"
        else:
            info += "No user records available.\n"
        performances = session.query(UserPerformance).all()
        if performances:
            avg_score = sum([p.performance_score for p in performances]) / len(performances)
            info += f"Overall Average Performance Score: {avg_score:.2f}.\n"
        else:
            info += "No performance data available.\n"
    else:
        info += "No role-specific context available.\n"
    
    session.close()
    return info

#db_context.py
import logging
import spacy
from sqlalchemy import desc
from models import SessionLocal, User, Transcript, PerformanceMetric as UserPerformance
from db_tool import get_employee_performance_by_name

logger = logging.getLogger(__name__)

# Load spaCy English model for name extraction
nlp = spacy.load("en_core_web_sm")

def extract_name(text: str) -> str:
    """
    Extracts a person's name from the given text using spaCy.
    """
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    return None

def retrieve_db_context(role: str, logged_in_user: str = None, query: str = None) -> str:
    """
    Retrieve context from the database based on the user's role and the target employee name.
    
    - For employees: Only the logged-in user's data is returned. If the query targets someone else,
      an access-denied message is returned.
    - For HR: If the query contains a name different from the logged-in user, that employee’s data is fetched.
      Otherwise, HR's own data or overall view is returned.
    - For managers: Recent meeting transcripts are fetched.
    """
    session = SessionLocal()
    info = ""
    
    target_employee = None
    if role.lower() == "hr":
        if query:
            extracted = extract_name(query)
            # If a name is extracted and it's different from the logged in user, use it.
            if extracted and (not logged_in_user or extracted.lower() != logged_in_user.lower()):
                target_employee = extracted
        # If no target is found, default to the logged in user.
        if not target_employee:
            target_employee = logged_in_user
    elif role.lower() == "employee":
        # Employees can only access their own data.
        target_employee = logged_in_user
        if query:
            extracted = extract_name(query)
            # If the extracted name differs from the logged in user, deny access.
            if extracted and extracted.lower() != logged_in_user.lower():
                session.close()
                return "As a simple employee, you do not have access to other employees' data."
    else:
        # For other roles (e.g., manager), default to the logged in user's context.
        target_employee = logged_in_user

    if role.lower() in ["employee", "hr"] and target_employee:
        # Fetch employee details using case-insensitive partial matching.
        user = session.query(User).filter(User.name.ilike(f"%{target_employee}%")).first()
        if user:
            logger.info(f"Found user: {user.name}")
            info += (f"Employee Profile: {user.name}, Email: {user.email}, "
                     f"Department: {user.department}, Role: {user.role}.\n")
            # Fetch performance data.
            performance_details = get_employee_performance_by_name(user.name)
            info += performance_details + "\n"
            # Retrieve recent transcript excerpts.
            transcripts = session.query(Transcript).filter(
                Transcript.speaker_label.ilike(f"%{user.name}%")
            ).order_by(desc(Transcript.created_at)).limit(3).all()
            if transcripts:
                excerpts = " | ".join([t.transcript[:50] for t in transcripts])
                info += f"Recent Transcript Excerpts: {excerpts}.\n"
            else:
                info += "No transcript excerpts found for this employee.\n"
        else:
            info += f"No record found for employee '{target_employee}'.\n"
    
    elif role.lower() == "manager":
        transcripts = session.query(Transcript).order_by(desc(Transcript.created_at)).limit(3).all()
        if transcripts:
            excerpts = " | ".join([t.transcript[:50] for t in transcripts])
            info += f"Recent Meeting Transcript Excerpts: {excerpts}.\n"
        else:
            info += "No recent transcripts available.\n"
    
    elif role.lower() == "hr" and not target_employee:
        users = session.query(User).all()
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

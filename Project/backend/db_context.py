# db_context.py
import logging
import spacy
from sqlalchemy import desc
from db_tool import get_employee_performance_by_name
from models import SessionLocal, User, Transcript, TranscriptLine  # TranscriptLine imported here

# Configure logging
logging.basicConfig(filename="db_context.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
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
    Retrieve context from the database based on the user's role and query.
    
    For HR:
      - If a query contains a name different from the logged-in user, return that employee's data.
      - Otherwise, return the full employee roster.
    
    For Managers:
      - Return a list of employees (subordinates) reporting to the logged-in manager.
      - Additionally, return recent transcript excerpts from the team.
    
    For Employees:
      - Return only their own data.
      - Deny access if the query targets another employee.
    """
    session = SessionLocal()
    info = ""
    try:
        if role.lower() == "hr":
            # If a query is provided, attempt to extract a target employee name
            if query:
                extracted = extract_name(query)
                if extracted and (not logged_in_user or extracted.lower() != logged_in_user.lower()):
                    user = session.query(User).filter(User.name.ilike(f"%{extracted}%")).first()
                    if user:
                        logger.info(f"HR query: Found user {user.name}")
                        role_text = user.role.name if user.role and hasattr(user.role, "name") else str(user.role)
                        info += (f"Employee Profile: {user.name}, Email: {user.email}, "
                                 f"Department: {user.department}, Role: {role_text}.\n")
                        perf = get_employee_performance_by_name(user.name)
                        info += perf + "\n"
                    else:
                        info += f"No record found for employee '{extracted}'.\n"
                    return info
            # If no specific target, return full employee roster
            users = session.query(User).all()
            if users:
                roster = " | ".join([f"{u.name} ({u.role.name if u.role and hasattr(u.role, 'name') else u.role})" for u in users])
                info += f"Employee Roster: {roster}.\n"
            else:
                info += "No employee records available.\n"
            return info
        
        elif role.lower() == "manager":
            # For managers, return employees who report to the logged-in manager.
            # Assumes User.manager_id and a backref 'subordinates' are set.
            manager = session.query(User).filter(User.name.ilike(f"%{logged_in_user}%")).first()
            if manager:
                if manager.subordinates:
                    roster = " | ".join([f"{u.name} ({u.email})" for u in manager.subordinates])
                    info += f"Employees working under you: {roster}.\n"
                    # Also retrieve transcript excerpts for each subordinate
                    transcript_excerpts = []
                    for subordinate in manager.subordinates:
                        # Retrieve the most recent transcript line where the subordinate is the speaker
                        lines = session.query(TranscriptLine).filter(TranscriptLine.speaker_label.ilike(f"%{subordinate.name}%"))\
                                        .order_by(desc(TranscriptLine.created_at)).limit(1).all()
                        for line in lines:
                            # Append a short excerpt
                            transcript_excerpts.append(f"{subordinate.name}: {line.text[:50]}")
                    if transcript_excerpts:
                        info += "Recent Transcript Excerpts from your team:\n" + " | ".join(transcript_excerpts) + "\n"
                else:
                    info += f"No employees found under you, {logged_in_user}.\n"
            else:
                info += f"No record found for manager '{logged_in_user}'.\n"
            return info
        
        elif role.lower() == "employee":
            # Employees can only access their own data.
            if query:
                extracted = extract_name(query)
                if extracted and extracted.lower() != logged_in_user.lower():
                    session.close()
                    return "You don't have access to this data."
            user = session.query(User).filter(User.name.ilike(f"%{logged_in_user}%")).first()
            if user:
                role_text = user.role.name if user.role and hasattr(user.role, "name") else str(user.role)
                info += (f"Employee Profile: {user.name}, Email: {user.email}, "
                         f"Department: {user.department}, Role: {role_text}.\n")
                perf = get_employee_performance_by_name(user.name)
                info += perf + "\n"
            else:
                info += f"No record found for employee '{logged_in_user}'.\n"
            return info
        
        else:
            info += "No role-specific context available.\n"
            return info
    finally:
        session.close()

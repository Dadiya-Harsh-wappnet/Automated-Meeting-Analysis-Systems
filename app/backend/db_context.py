import logging
import spacy
from sqlalchemy import desc
from typing import Optional

from db_tool import get_employee_performance_by_name
from models import SessionLocal, User, Transcript, TranscriptLine

# Configure logging
logging.basicConfig(
    filename="db_context.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.error("Failed to load spaCy model: %s", e)
    raise

def extract_name(text: str) -> Optional[str]:
    """
    Extract a person's name from the given text.
    """
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    return None

def retrieve_db_context(role: str, logged_in_user: str = None, query: str = None) -> str:
    """
    Retrieve database context based on role.
    
    - **HR:** If a query targets another employee, return that employee's profile and performance; otherwise, return a full roster.
    - **Manager:** Return subordinates and recent transcript excerpts.
    - **Employee:** Return personal data.
    """
    session = SessionLocal()
    info = ""
    try:
        if role.lower() == "hr":
            if query:
                extracted = extract_name(query)
                if extracted and (not logged_in_user or extracted.lower() != logged_in_user.lower()):
                    user = session.query(User).filter(User.name.ilike(f"%{extracted}%")).first()
                    if user:
                        logger.info("HR query: Found user %s", user.name)
                        role_text = user.role.name if user.role and hasattr(user.role, "name") else str(user.role)
                        info += (f"Employee Profile: {user.name}, Email: {user.email}, "
                                 f"Department: {user.department}, Role: {role_text}.\n")
                        perf = get_employee_performance_by_name(user.name)
                        info += perf + "\n"
                    else:
                        info += f"No record found for employee '{extracted}'.\n"
                    return info
            users = session.query(User).all()
            if users:
                roster = " | ".join([f"{u.name} ({u.role.name if u.role and hasattr(u.role, 'name') else u.role})" for u in users])
                info += f"Employee Roster: {roster}.\n"
            else:
                info += "No employee records available.\n"
            return info

        elif role.lower() == "manager":
            manager = session.query(User).filter(User.name.ilike(f"%{logged_in_user}%")).first()
            if manager:
                if manager.subordinates:
                    roster = " | ".join([f"{emp.name} ({emp.email})" for emp in manager.subordinates])
                    info += f"Employees working under you: {roster}.\n"
                    transcript_excerpts = []
                    for subordinate in manager.subordinates:
                        lines = (session.query(TranscriptLine)
                                     .filter(TranscriptLine.speaker_label.ilike(f"%{subordinate.name}%"))
                                     .order_by(desc(TranscriptLine.created_at))
                                     .limit(1)
                                     .all())
                        for line in lines:
                            transcript_excerpts.append(f"{subordinate.name}: {line.text[:50]}")
                    if transcript_excerpts:
                        info += "Recent Transcript Excerpts from your team:\n" + " | ".join(transcript_excerpts) + "\n"
                else:
                    info += f"No employees found under you, {logged_in_user}.\n"
            else:
                info += f"No record found for manager '{logged_in_user}'.\n"
            return info

        elif role.lower() == "employee":
            if query:
                extracted = extract_name(query)
                if extracted and extracted.lower() != logged_in_user.lower():
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
    except Exception as ex:
        logger.error("Error retrieving DB context: %s", ex)
        return "An error occurred while retrieving context."
    finally:
        session.close()

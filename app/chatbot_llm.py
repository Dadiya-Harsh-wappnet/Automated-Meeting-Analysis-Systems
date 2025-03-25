# chatbot_llm.py
import re
from db import get_recent_meeting_transcripts

def generate_response(query, role=None, user_name=None):
    """
    Generate a default chatbot response.
    If the query references a meeting (e.g., "meeting 123"), return that transcript.
    Otherwise, return a default response.
    """
    match = re.search(r"meeting\s*(\d+)", query, re.IGNORECASE)
    if match:
        meeting_id = int(match.group(1))
        return get_recent_meeting_transcripts(meeting_id)
    else:
        return f"Chatbot response for query: '{query}'"

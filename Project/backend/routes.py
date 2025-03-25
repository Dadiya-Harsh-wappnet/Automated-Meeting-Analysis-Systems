from flask import Blueprint, request, jsonify
from models import db, User, Meeting, Transcript, TranscriptLine, PerformanceMetric, Task
from chatbot import process_chat_query

api = Blueprint("api", __name__)

@api.route("/api/meetings", methods=["GET"])
def get_meetings():
    meetings = Meeting.query.all()
    meetings_data = [{
        "meeting_id": m.meeting_id,
        "title": m.title,
        "description": m.description,
        "scheduled_start": m.scheduled_start,
        "scheduled_end": m.scheduled_end
    } for m in meetings]
    return jsonify(meetings_data), 200

@api.route("/api/transcripts/<int:meeting_id>", methods=["GET"])
def get_transcript(meeting_id):
    transcript = Transcript.query.filter_by(meeting_id=meeting_id).first()
    if transcript:
        return jsonify({
            "transcript_id": transcript.transcript_id,
            "transcript_text": transcript.transcript_text,
            "lines": [{
                "line_id": line.line_id,
                "speaker_label": line.speaker_label,
                "text": line.text,
                "start_time": line.start_time,
                "end_time": line.end_time,
                "sentiment_score": str(line.sentiment_score) if line.sentiment_score is not None else None
            } for line in transcript.lines]
        }), 200
    return jsonify({"error": "Transcript not found"}), 404

@api.route("/api/chatbot", methods=["POST"])
def chatbot_query():
    data = request.json
    user_role = data.get("role")  # e.g., "HR", "Manager", "Employee"
    query = data.get("query")
    if not user_role or not query:
        return jsonify({"error": "role and query are required"}), 400

    response_text = process_chat_query(user_role, query)
    return jsonify({"response": response_text}), 200

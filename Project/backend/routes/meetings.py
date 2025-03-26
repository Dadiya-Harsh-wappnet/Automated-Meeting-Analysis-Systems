# backend/routes/meetings.py
from flask import Blueprint, request, jsonify
from models import SessionLocal, Meeting, Transcript, TranscriptLine, PerformanceMetric, Task
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

meetings_bp = Blueprint("meetings_bp", __name__)

# Create a new meeting
@meetings_bp.route('/create', methods=['POST'])
@jwt_required()
def create_meeting():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    google_meet_link = data.get("google_meet_link")  # This would come from integration
    scheduled_start = data.get("scheduled_start")
    scheduled_end = data.get("scheduled_end")

    session = SessionLocal()
    try:
        if not title:
            return jsonify({"msg": "Meeting title is required"}), 400

        user_id = get_jwt_identity()
        meeting = Meeting(
            title=title,
            description=description,
            google_meet_link=google_meet_link,
            scheduled_start=datetime.fromisoformat(scheduled_start) if scheduled_start else None,
            scheduled_end=datetime.fromisoformat(scheduled_end) if scheduled_end else None,
            created_by=user_id
        )
        session.add(meeting)
        session.commit()
    finally:
        session.close()
    return jsonify({"msg": "Meeting created successfully", "meeting_id": meeting.id}), 201

# Get all meetings for the logged-in user
@meetings_bp.route('/', methods=['GET'])
@jwt_required()
def get_meetings():
    user_id = get_jwt_identity()
    session = SessionLocal()
    try:
        meetings = session.query(Meeting).filter_by(created_by=user_id).all()
        meetings_list = [{
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "google_meet_link": m.google_meet_link,
            "scheduled_start": m.scheduled_start.isoformat() if m.scheduled_start else None,
            "scheduled_end": m.scheduled_end.isoformat() if m.scheduled_end else None
        } for m in meetings]
    finally:
        session.close()
    return jsonify(meetings_list), 200

# Stub for uploading transcript data (combined and line-by-line)
@meetings_bp.route('/transcript/<int:meeting_id>', methods=['POST'])
@jwt_required()
def upload_transcript(meeting_id):
    data = request.get_json()
    transcript_text = data.get("transcript_text")
    lines = data.get("lines", [])  # Expecting a list of {speaker_label, start_time, end_time, text, sentiment_score}
    
    session = SessionLocal()

    try:
        transcript = Transcript(meeting_id=meeting_id, transcript_text=transcript_text)
        session.add(transcript)
        session.flush()  # Get transcript id without commit

        for line in lines:
            transcript_line = TranscriptLine(
                transcript_id=transcript.id,
                speaker_label=line.get("speaker_label"),
                start_time=datetime.fromisoformat(line.get("start_time")) if line.get("start_time") else None,
                end_time=datetime.fromisoformat(line.get("end_time")) if line.get("end_time") else None,
                text=line.get("text"),
                sentiment_score=line.get("sentiment_score")
            )
            session.add(transcript_line)
        session.commit()
    finally:
        session.close()
    return jsonify({"msg": "Transcript uploaded"}), 201

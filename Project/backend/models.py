from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = "roles"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False)

class Department(db.Model):
    __tablename__ = "departments"
    department_id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False)

class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
    manager_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    role = db.relationship("Role", backref="users")
    department = db.relationship("Department", backref="users")
    manager = db.relationship("User", remote_side=[user_id], backref="reports")

class Meeting(db.Model):
    __tablename__ = "meetings"
    meeting_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    scheduled_start = db.Column(db.DateTime)
    scheduled_end = db.Column(db.DateTime)
    actual_start = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship("User", backref="created_meetings")

class MeetingParticipant(db.Model):
    __tablename__ = "meeting_participants"
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.meeting_id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    participant_role = db.Column(db.String(50))  # e.g., "Host", "Attendee"
    joined_at = db.Column(db.DateTime)
    left_at = db.Column(db.DateTime)

class Transcript(db.Model):
    __tablename__ = "transcripts"
    transcript_id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.meeting_id", ondelete="CASCADE"), nullable=False)
    transcript_text = db.Column(db.Text)  # Combined transcript for quick display.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meeting = db.relationship("Meeting", backref="transcript")

class TranscriptLine(db.Model):
    __tablename__ = "transcript_lines"
    line_id = db.Column(db.Integer, primary_key=True)
    transcript_id = db.Column(db.Integer, db.ForeignKey("transcripts.transcript_id", ondelete="CASCADE"), nullable=False)
    speaker_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    speaker_label = db.Column(db.String(50))  # e.g., "Speaker 1"
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    text = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Numeric(3,2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transcript = db.relationship("Transcript", backref="lines")
    speaker = db.relationship("User", backref="transcript_lines")

class PerformanceMetric(db.Model):
    __tablename__ = "performance_metrics"
    metric_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.meeting_id"))
    metric_type = db.Column(db.String(50), nullable=False)  # e.g., "speaking_time"
    metric_value = db.Column(db.Numeric(10,2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="performance_metrics")
    meeting = db.relationship("Meeting", backref="performance_metrics")

class Task(db.Model):
    __tablename__ = "tasks"
    task_id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.meeting_id", ondelete="CASCADE"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Open")  # e.g., "Open", "Done"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting = db.relationship("Meeting", backref="tasks")
    assignee = db.relationship("User", backref="tasks")

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ----- Role -----
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# ----- Department -----
class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# ----- User -----
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = db.relationship("Role", backref="users")
    department = db.relationship("Department", backref="users")
    manager = db.relationship("User", remote_side=[id], backref="reports")

# ----- Meeting -----
class Meeting(db.Model):
    __tablename__ = "meetings"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    scheduled_start = db.Column(db.DateTime)
    scheduled_end = db.Column(db.DateTime)
    actual_start = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)
    google_meet_link = db.Column(db.String(300))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship("User", backref="created_meetings")

# ----- Meeting Participants -----
class MeetingParticipant(db.Model):
    __tablename__ = "meeting_participants"
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = db.Column(db.String(50))  # e.g., Host, Attendee
    joined_at = db.Column(db.DateTime)
    left_at = db.Column(db.DateTime)

# ----- Transcript -----
class Transcript(db.Model):
    __tablename__ = "transcripts"
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    transcript_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meeting = db.relationship("Meeting", backref="transcript")

# ----- Transcript Line -----
class TranscriptLine(db.Model):
    __tablename__ = "transcript_lines"
    id = db.Column(db.Integer, primary_key=True)
    transcript_id = db.Column(db.Integer, db.ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    speaker_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    speaker_label = db.Column(db.String(50))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    text = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Numeric(3,2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transcript = db.relationship("Transcript", backref="lines")
    speaker = db.relationship("User", backref="transcript_lines")

# ----- Performance Metric -----
class PerformanceMetric(db.Model):
    __tablename__ = "performance_metrics"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.id"))
    metric_type = db.Column(db.String(50), nullable=False)
    metric_value = db.Column(db.Numeric(10,2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="performance_metrics")
    meeting = db.relationship("Meeting", backref="performance_metrics")

# ----- Task (Action Items) -----
class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.id", ondelete="CASCADE"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting = db.relationship("Meeting", backref="tasks")
    assignee = db.relationship("User", backref="tasks")
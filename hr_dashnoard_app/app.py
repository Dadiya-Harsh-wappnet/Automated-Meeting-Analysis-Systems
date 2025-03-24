# app.py
import os
from flask import Flask, render_template
from models import get_session, User, Meeting, MeetingParticipant, MeetingTranscript
from analysis import meeting_transcript_summary, employee_participation_summary, generate_bar_plot, generate_line_plot, generate_meeting_participation_plot


from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

# Update the db_url with your PostgreSQL credentials
db_url = os.getenv("db_url", "postgresql://postgres:password@localhost:5433/AMAS")
if db_url is None:
    raise ValueError("Database URL not provided. Please set the db_url environment variable.")
session = get_session(db_url)

@app.route("/")
def index():
    return "<h1>Welcome to the AMAS HR Dashboard</h1>"

@app.route("/hr/dashboard")
def hr_dashboard():
    # Retrieve data from the database
    users = session.query(User).all()
    meetings = session.query(Meeting).all()
    participants = session.query(MeetingParticipant).all()
    transcripts = session.query(MeetingTranscript).all()
    
    # Build a simple lookup for users: user_id -> name
    users_lookup = {u.id: u.name for u in users}
    
    # Prepare user details for the dashboard table
    user_details = [{
        "id": u.id,
        "name": u.name,
        "role": u.role,
        "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else ""
    } for u in users]
    
    # Compute meeting transcripts summary
    transcript_count, avg_duration = meeting_transcript_summary(transcripts)
    
    # Compute employee participation counts
    participation_dict = employee_participation_summary(participants)
    
    # Ensure static/plots directory exists
    os.makedirs("static/plots", exist_ok=True)
    
    # Generate a bar plot for meeting participation per user
    participation_plot_path = "static/plots/participation.png"
    generate_meeting_participation_plot(participation_dict, users_lookup, participation_plot_path)
    
    # Generate a line plot: transcript count per meeting
    # Compute transcript count for each meeting
    meeting_transcript_counts = {}
    for t in transcripts:
        meeting_transcript_counts[t.meeting_id] = meeting_transcript_counts.get(t.meeting_id, 0) + 1
    meeting_ids = []
    transcript_counts = []
    for m in meetings:
        meeting_ids.append(str(m.id))
        transcript_counts.append(meeting_transcript_counts.get(m.id, 0))
    line_plot_path = "static/plots/transcripts_over_meetings.png"
    generate_line_plot(meeting_ids, transcript_counts, "Transcript Count per Meeting", line_plot_path)
    
    # Prepare a textual summary
    summary_text = (
        f"Total Users: {len(users)}\n"
        f"Total Meetings: {len(meetings)}\n"
        f"Total Transcript Entries: {transcript_count}\n"
        f"Average Transcript Duration: {avg_duration:.2f} sec\n"
    )
    
    return render_template("hr_dashboard.html",
                           summary_text=summary_text,
                           user_details=user_details,
                           participation_plot="participation.png",
                           line_plot="transcripts_over_meetings.png")

if __name__ == "__main__":
    app.run(debug=True)

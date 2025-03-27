import os
import json
from datetime import datetime, timedelta
from celery import Celery
from dotenv import load_dotenv

from models import SessionLocal, Meeting
from db_tool import auto_generate_tasks_from_transcript

# Load environment variables
load_dotenv()

celery_app = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
)
celery_app.conf.timezone = 'UTC'

# Configure Celery Beat to run the job once a week (604800 seconds = 7 days)
celery_app.conf.beat_schedule = {
    'process-weekly-meetings': {
        'task': 'worker.process_weekly_meetings',
        'schedule': 604800.0,  # 7 days in seconds
    },
}

@celery_app.task
def process_weekly_meetings():
    """
    Task that scans meetings from the past week and auto-generates tasks by processing transcripts.
    """
    session = SessionLocal()
    try:
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        meetings = session.query(Meeting).filter(Meeting.created_at >= one_week_ago).all()
        for meeting in meetings:
            tasks_generated = auto_generate_tasks_from_transcript(meeting.id, session=session)
            if tasks_generated:
                print(f"Generated tasks for meeting {meeting.id}: {json.dumps(tasks_generated)}")
        session.commit()
    except Exception as e:
        session.rollback()
        print("Error processing weekly meetings:", e)
    finally:
        session.close()

if __name__ == '__main__':
    # For testing, you can trigger the task directly:
    process_weekly_meetings.delay()

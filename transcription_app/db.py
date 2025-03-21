from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://your_db_user:your_db_password@localhost/your_db_name")
Base = declarative_base()

class Transcript(Base):
    __tablename__ = 'transcripts'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(String(50), nullable=True)  # You can provide a meeting ID if available.
    speaker_label = Column(String(100))
    transcript = Column(Text)
    start_time = Column(Float, nullable=True)  # e.g., seconds into the video.
    end_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def insert_transcript_lines_sqlalchemy(db_url = DB_URL, transcript_lines=[]):
    """
    Insert transcript lines into the PostgreSQL database using SQLAlchemy.
    
    Each transcript_line in transcript_lines should be a dictionary with keys:
      - meeting_id (optional)
      - speaker_label (e.g., "Interviewer - Speaker 1")
      - transcript (the text content)
      - start_time (float)
      - end_time (float)
    """
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)  # Create table if it doesn't exist.
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        for line in transcript_lines:
            transcript_entry = Transcript(
                meeting_id=line.get('meeting_id'),
                speaker_label=line.get('speaker_label'),
                transcript=line.get('transcript'),
                start_time=line.get('start_time'),
                end_time=line.get('end_time')
            )
            session.add(transcript_entry)
        session.commit()
        print("Transcript lines inserted successfully using SQLAlchemy!")
    except Exception as e:
        session.rollback()
        print(f"Error inserting transcript lines: {e}")
    finally:
        session.close()

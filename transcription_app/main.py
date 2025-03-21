# -*- coding: utf-8 -*-

### **File: main.py**


import os
import sys
import argparse
from video_processor import convert_video_to_audio, transcribe_audio
from vad_processor import load_silero_vad, get_speech_embeddings, cluster_speakers, assign_transcript_to_speakers
from role_assigner import assign_roles, save_formatted_transcript
from db import insert_transcript_lines_sqlalchemy

def parse_transcript_file(transcript_file):
    """
    Parse the transcript file and create a list of dictionaries for insertion.
    Each line in the transcript is assumed to be in the format:
      [Role] Speaker Label: Transcript text
    The function extracts:
      - role: text within the square brackets
      - speaker_label: text between the square bracket and the colon
      - transcript: text after the colon.
    Since no meeting_id, start_time, or end_time information is available, these will be set to None.
    """
    transcript_lines = []
    with open(transcript_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Find the role in square brackets
            if line.startswith('['):
                try:
                    role_end = line.index(']')
                    role = line[1:role_end]
                except ValueError:
                    role = "Unknown"
            else:
                role = "Unknown"
            
            # Split at the colon
            if ':' in line:
                header, transcript_text = line.split(':', 1)
            else:
                header, transcript_text = line, ""
            
            # Remove the role part from header to get the speaker label
            speaker_label = header.replace(f'[{role}]', '').strip()
            
            transcript_lines.append({
                "meeting_id": None,
                "speaker_label": f"{role} - {speaker_label}",
                "transcript": transcript_text.strip(),
                "start_time": None,
                "end_time": None
            })
    return transcript_lines

def main():
    parser = argparse.ArgumentParser(
        description="Generate role-based speaker transcripts from a video file and store in PostgreSQL"
    )
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--output", default="role_transcript.txt", help="Output transcript file path")
    parser.add_argument("--min-speakers", type=int, default=2, help="Minimum number of speakers to detect")
    parser.add_argument("--max-speakers", type=int, default=2, help="Maximum number of speakers to detect")
    parser.add_argument("--db_url", default="postgresql+psycopg2://user:1234@192.168.10.132:5432/amas",
                        help="Database URL for PostgreSQL")
    
    args = parser.parse_args()
    
    # Create temporary directory for audio extraction
    os.makedirs("temp", exist_ok=True)
    audio_path = os.path.join("temp", os.path.basename(args.video_path) + ".wav")
    
    # Step 1: Extract audio from video
    if not convert_video_to_audio(args.video_path, audio_path):
        sys.exit(1)
    
    # Step 2: Transcribe audio using Whisper
    transcription = transcribe_audio(audio_path, args.model)
    if transcription is None:
        sys.exit(1)
    
    # Step 3: Load Silero VAD
    vad_model, get_speech_timestamps, read_audio = load_silero_vad()
    if vad_model is None:
        print("Silero VAD failed to load. Exiting.")
        sys.exit(1)
    
    # Step 4: Get speech embeddings and segments using VAD
    embeddings, vad_segments = get_speech_embeddings(audio_path, vad_model, get_speech_timestamps, read_audio)
    if embeddings is None or len(embeddings) == 0:
        print("No speech segments detected. Exiting.")
        sys.exit(1)
    
    # Step 5: Cluster segments to assign speaker labels
    vad_segments = cluster_speakers(embeddings, vad_segments,
                                    min_speakers=args.min_speakers,
                                    max_speakers=args.max_speakers)
    
    # Step 6: Assign Whisper transcript segments to speakers based on time overlap
    segments_with_speakers = assign_transcript_to_speakers(transcription["segments"], vad_segments)
    
    # Step 7: Assign roles using a simple heuristic (e.g., based on question counts)
    segments_with_roles = assign_roles(segments_with_speakers)
    
    # Step 8: Save the formatted transcript and retrieve transcript lines
    transcript_lines = save_formatted_transcript(segments_with_roles, args.output)
    
    # Clean up temporary audio file
    os.remove(audio_path)
    print("\nProcessing completed successfully!")


    transcript_lines = parse_transcript_file(args.output)

    # Step 9: Insert transcript lines into PostgreSQL using SQLAlchemy
    insert_transcript_lines_sqlalchemy(args.db_url, transcript_lines)

if __name__ == "__main__":
    main()

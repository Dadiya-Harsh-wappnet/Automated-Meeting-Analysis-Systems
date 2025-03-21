import os
import sys
import argparse
import torch
import whisper
from pydub import AudioSegment
import re

def convert_video_to_audio(video_path, audio_path):
    """Extract audio from video file."""
    try:
        # Check if the video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Use ffmpeg through pydub to extract audio
        video = AudioSegment.from_file(video_path)
        video.export(audio_path, format="mp3")
        print(f"Audio extracted successfully to {audio_path}")
        return True
    except Exception as e:
        print(f"Error converting video to audio: {e}")
        return False

def transcribe_audio(audio_path, model_name="base"):
    """Transcribe audio using Whisper model."""
    try:
        # Load the Whisper model
        print(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)
        
        # Transcribe the audio
        print("Transcribing audio...")
        result = model.transcribe(audio_path, verbose=True)
        
        return result
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def simple_speaker_detection(segments):
    """Simple heuristic-based speaker detection from Whisper segments."""
    # Initialize speaker information
    processed_segments = []
    current_speaker = 1
    previous_was_question = False
    
    for segment in segments:
        text = segment["text"].strip()
        
        # Create a new segment with speaker info
        new_segment = {
            "text": text,
            "start": segment["start"],
            "end": segment["end"]
        }
        
        # Simple heuristic rules for speaker detection
        # 1. If previous segment was a question, change speaker
        if previous_was_question:
            current_speaker = 2 if current_speaker == 1 else 1
            previous_was_question = False
            
        # 2. Check if current segment is a question
        if text.endswith('?'):
            previous_was_question = True
            
        # 3. Change speaker if there's a pause (> 1 second)
        if processed_segments and (segment["start"] - processed_segments[-1]["end"]) > 1.0:
            current_speaker = 2 if current_speaker == 1 else 1
            
        # 4. Change speaker for short responses (likely dialogue)
        if processed_segments and len(text.split()) < 5 and processed_segments[-1]["speaker"] != current_speaker:
            # Keep the short response speaker different from the previous one
            pass
        elif processed_segments and len(text.split()) < 5:
            # For other short responses, alternate speakers
            current_speaker = 2 if current_speaker == 1 else 1
            
        # Apply speaker label
        new_segment["speaker"] = f"Speaker {current_speaker}"
        processed_segments.append(new_segment)
        
    return processed_segments

def detect_named_speakers(transcript):
    """Detect if there are named speakers in the transcript."""
    # Common patterns for named speakers
    patterns = [
        r'([A-Z][a-z]+):', 
        r'([A-Z][a-z]+) -',
        r'([A-Z][a-z]+)(?:\s+says:)'
    ]
    
    # Extract potential speaker names
    potential_speakers = []
    for pattern in patterns:
        matches = re.findall(pattern, transcript)
        potential_speakers.extend(matches)
    
    # Filter out common false positives
    false_positives = ['I', 'The', 'It', 'This', 'That', 'There', 'They', 'We', 'You', 'He', 'She']
    speakers = [s for s in potential_speakers if s not in false_positives]
    
    # Count occurrences
    speaker_counts = {}
    for speaker in speakers:
        if speaker in speaker_counts:
            speaker_counts[speaker] += 1
        else:
            speaker_counts[speaker] = 1
    
    # Only consider names that appear multiple times (likely actual speakers)
    valid_speakers = {k: v for k, v in speaker_counts.items() if v >= 2}
    
    return valid_speakers

def map_speakers_to_segments(segments, speaker_names=None):
    """Map generic Speaker 1, Speaker 2 to actual names if detected."""
    if not speaker_names or len(speaker_names) < 2:
        return segments
    
    # Map generic speakers to detected names
    speaker_map = {}
    for i, name in enumerate(list(speaker_names.keys())[:2]):
        speaker_map[f"Speaker {i+1}"] = name
    
    # Apply the mapping
    for segment in segments:
        generic_speaker = segment.get("speaker")
        if generic_speaker in speaker_map:
            segment["speaker"] = speaker_map[generic_speaker]
    
    return segments

def save_formatted_transcript(segments, output_file):
    """Save the transcript in a formatted way with speaker labels."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            current_speaker = None
            current_text = ""
            
            for segment in segments:
                speaker = segment.get("speaker", "Unknown")
                text = segment.get("text", "").strip()
                
                # If speaker changes, write the previous speaker's text
                if speaker != current_speaker and current_text:
                    f.write(f"{current_speaker}: {current_text}\n")
                    current_text = ""
                
                # Update current speaker and add text
                current_speaker = speaker
                current_text += (" " + text if current_text else text)
            
            # Write the last speaker's text
            if current_text:
                f.write(f"{current_speaker}: {current_text}\n")
                
        print(f"Speaker-separated transcript saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate speaker-separated transcripts from video files using Whisper")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"], 
                        help="Whisper model size (default: base)")
    parser.add_argument("--output", default="transcript.txt", help="Output transcript file path")
    
    args = parser.parse_args()
    
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    
    # Extract audio from video
    audio_path = os.path.join("temp", os.path.basename(args.video_path) + ".mp3")
    if not convert_video_to_audio(args.video_path, audio_path):
        sys.exit(1)
    
    # Transcribe audio with Whisper
    transcription = transcribe_audio(audio_path, args.model)
    if transcription is None:
        sys.exit(1)
    
    # Check for named speakers in full transcript
    detected_speakers = detect_named_speakers(transcription["text"])
    print(f"Detected potential speaker names: {list(detected_speakers.keys()) if detected_speakers else 'None'}")
    
    # Process segments with simple speaker detection
    segments_with_speakers = simple_speaker_detection(transcription["segments"])
    
    # Map generic speakers to detected names if available
    if detected_speakers:
        segments_with_speakers = map_speakers_to_segments(segments_with_speakers, detected_speakers)
    
    # Save formatted transcript
    save_formatted_transcript(segments_with_speakers, args.output)
    
    # Clean up
    os.remove(audio_path)
    print("\nProcess completed successfully!")

if __name__ == "__main__":
    main()
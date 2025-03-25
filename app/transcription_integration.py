# transcription_integration.py
import os
from main import parse_transcript_file, convert_video_to_audio, transcribe_audio
from vad_processor import load_silero_vad, get_speech_embeddings, cluster_speakers, assign_transcript_to_speakers
from role_assigner import assign_roles, save_formatted_transcript

def run_transcription_pipeline(video_path, model_size="base", min_speakers=2, max_speakers=2, output="role_transcript.txt"):
    """
    Run the transcription and speaker diarization pipeline.
    Returns a list of transcript lines (dictionaries).
    """
    os.makedirs("temp", exist_ok=True)
    audio_path = os.path.join("temp", os.path.basename(video_path) + ".wav")
    
    # Step 1: Convert video to audio.
    if not convert_video_to_audio(video_path, audio_path):
        raise Exception("Video-to-audio conversion failed")
    
    # Step 2: Transcribe audio using Whisper.
    transcription = transcribe_audio(audio_path, model_size)
    if transcription is None:
        raise Exception("Transcription failed")
    
    # Step 3: Load Silero VAD.
    vad_model, get_speech_timestamps, read_audio = load_silero_vad()
    if vad_model is None:
        raise Exception("Silero VAD failed to load")
    
    # Step 4: Get speech embeddings and segments.
    embeddings, vad_segments = get_speech_embeddings(audio_path, vad_model, get_speech_timestamps, read_audio)
    if embeddings is None or len(embeddings) == 0:
        raise Exception("No speech segments detected")
    
    # Step 5: Cluster segments to assign speaker labels.
    vad_segments = cluster_speakers(embeddings, vad_segments, min_speakers, max_speakers)
    
    # Step 6: Align transcript segments with VAD segments.
    segments_with_speakers = assign_transcript_to_speakers(transcription["segments"], vad_segments)
    
    # Step 7: Assign roles to segments.
    segments_with_roles = assign_roles(segments_with_speakers)
    
    # Step 8: Save the formatted transcript.
    save_formatted_transcript(segments_with_roles, output)
    
    # Clean up the temporary audio file.
    os.remove(audio_path)
    
    # Parse the output transcript file.
    transcript_lines = parse_transcript_file(output)
    return transcript_lines

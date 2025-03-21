import os
import sys
import argparse
import datetime
import torch
import whisper
import numpy as np
from pydub import AudioSegment
import torchaudio
from glob import glob
import torch.nn.functional as F
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

# --- Audio & Video Processing Functions ---

def convert_video_to_audio(video_path, audio_path):
    """
    Extract audio from a video file and save as a WAV file.
    Converts to mono and 16kHz sample rate.
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        video = AudioSegment.from_file(video_path)
        video = video.set_channels(1)  # Mono
        video = video.set_frame_rate(16000)  # 16kHz
        video.export(audio_path, format="wav")
        print(f"Audio extracted successfully to {audio_path}")
        return True
    except Exception as e:
        print(f"Error converting video to audio: {e}")
        return False

def transcribe_audio(audio_path, model_name="base"):
    """
    Transcribe the audio using the Whisper model.
    Returns the full transcription result including segments.
    """
    try:
        print(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)
        print("Transcribing audio...")
        result = model.transcribe(audio_path, verbose=True)
        return result
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

# --- Voice Activity Detection (VAD) Functions using Silero ---

def load_silero_vad():
    """
    Load the Silero VAD model for speech detection.
    Returns the model and helper functions.
    """
    try:
        print("Loading Silero VAD model...")
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                      model='silero_vad',
                                      force_reload=True,
                                      onnx=False)
        (get_speech_timestamps, _, read_audio, _, _) = utils
        return model, get_speech_timestamps, read_audio
    except Exception as e:
        print(f"Error loading Silero VAD: {e}")
        return None, None, None

def get_speech_embeddings(audio_path, vad_model, get_speech_timestamps, read_audio):
    """
    Detect speech segments from the audio using Silero VAD and compute simple embeddings.
    Returns an array of embeddings and a list of segment dictionaries.
    """
    try:
        wav = read_audio(audio_path, sampling_rate=16000)
        speech_timestamps = get_speech_timestamps(wav, vad_model, sampling_rate=16000, 
                                                    min_speech_duration_ms=500, 
                                                    max_speech_duration_s=float('inf'),
                                                    min_silence_duration_ms=500)
        print(f"Detected {len(speech_timestamps)} speech segments")
        
        embeddings = []
        segments = []
        
        def get_speech_segment(start_sample, end_sample):
            return wav[start_sample:end_sample]
        
        for i, segment in enumerate(speech_timestamps):
            start_sample = segment['start']
            end_sample = segment['end']
            speech_segment = get_speech_segment(start_sample, end_sample)
            
            if len(speech_segment) < 1600:  # Skip very short segments
                continue
            
            segment_tensor = torch.tensor(speech_segment).float()
            spec = torch.stft(
                segment_tensor,
                n_fft=512,
                hop_length=160,
                win_length=400,
                window=torch.hann_window(400),
                return_complex=True
            )
            spec = torch.abs(spec)
            
            # Compute mean energy over defined frequency bands
            freq_bands = [(0, 10), (10, 20), (20, 50), (50, 100), (100, 256)]
            feature_vector = []
            for low, high in freq_bands:
                band_energy = torch.mean(spec[low:high, :]).item()
                feature_vector.append(band_energy)
            
            # Temporal features: zero crossing rate and overall energy
            zero_crossings = torch.sum(torch.abs(torch.sign(segment_tensor[1:]) - torch.sign(segment_tensor[:-1]))).item() / 2
            zero_crossing_rate = zero_crossings / len(segment_tensor)
            feature_vector.append(zero_crossing_rate)
            energy = torch.mean(torch.abs(segment_tensor)).item()
            feature_vector.append(energy)
            
            start_time = start_sample / 16000
            end_time = end_sample / 16000
            
            embeddings.append(feature_vector)
            segments.append({
                'start': start_time, 
                'end': end_time, 
                'length': end_time - start_time
            })
        
        return np.array(embeddings), segments
    except Exception as e:
        print(f"Error extracting speech embeddings: {e}")
        return None, None

def cluster_speakers(embeddings, segments, min_speakers=2, max_speakers=5):
    """
    Cluster speech segments based on computed embeddings to differentiate speakers.
    Returns segments with an assigned speaker label.
    """
    if len(embeddings) == 0:
        print("No speech segments detected")
        return []
    
    embeddings = (embeddings - np.mean(embeddings, axis=0)) / (np.std(embeddings, axis=0) + 1e-8)
    
    best_score = -1
    best_labels = None
    best_n_clusters = min_speakers
    max_speakers = min(max_speakers, len(embeddings))
    
    for n_clusters in range(min_speakers, max_speakers + 1):
        if n_clusters >= len(embeddings):
            continue
        
        clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
        labels = clustering.fit_predict(embeddings)
        if n_clusters == 1 or len(set(labels)) <= 1:
            continue
        
        score = silhouette_score(embeddings, labels)
        print(f"Clusters: {n_clusters}, Silhouette Score: {score:.3f}")
        
        if score > best_score:
            best_score = score
            best_labels = labels
            best_n_clusters = n_clusters
    
    # Assign speaker labels to segments (Speaker 1, Speaker 2, etc.)
    for i, segment in enumerate(segments):
        if i < len(best_labels):
            segment['speaker'] = f"Speaker {best_labels[i] + 1}"
    
    print(f"Selected {best_n_clusters} speakers with silhouette score: {best_score:.3f}")
    return segments

def assign_transcript_to_speakers(whisper_segments, vad_segments):
    """
    Align Whisper transcript segments with the speech segments detected by VAD,
    assigning speaker labels to each transcript segment.
    """
    for w_segment in whisper_segments:
        w_start = w_segment['start']
        w_end = w_segment['end']
        best_overlap = 0
        best_speaker = "Unknown"
        for v_segment in vad_segments:
            v_start = v_segment['start']
            v_end = v_segment['end']
            overlap_start = max(w_start, v_start)
            overlap_end = min(w_end, v_end)
            if overlap_end > overlap_start:
                overlap_duration = overlap_end - overlap_start
                if overlap_duration > best_overlap:
                    best_overlap = overlap_duration
                    if 'speaker' in v_segment:
                        best_speaker = v_segment['speaker']
        w_segment['speaker'] = best_speaker
    return whisper_segments

# --- Role Assignment Layer ---

def assign_roles(segments):
    """
    A simple heuristic to assign conversation roles based on speaker utterances.
    This example uses a simple rule:
      - For each speaker, count the number of question marks in their combined text.
      - The speaker with the most questions is designated as the "Interviewer"
      - All others are labeled "Interviewee"
    
    You can extend this logic or integrate an ML model for role classification.
    """
    # Combine texts for each speaker.
    speaker_texts = {}
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        text = seg.get('text', '')
        speaker_texts[speaker] = speaker_texts.get(speaker, "") + " " + text
    
    # Count question marks per speaker.
    question_counts = {speaker: text.count('?') for speaker, text in speaker_texts.items()}
    
    # Determine the speaker with maximum questions (if any).
    if question_counts:
        interviewer = max(question_counts, key=question_counts.get)
    else:
        interviewer = None
    
    # Assign roles to each segment.
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        if speaker == interviewer and question_counts.get(interviewer, 0) > 0:
            seg['role'] = "Interviewer"
        else:
            seg['role'] = "Interviewee"
    
    return segments

# --- Transcript Saving ---

def save_formatted_transcript(segments, output_file):
    """
    Save the transcript with speaker labels and assigned roles in a formatted text file.
    Each line contains the role and speaker followed by their spoken text.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            current_role = None
            current_speaker = None
            current_text = ""
            for seg in segments:
                role = seg.get('role', 'Unknown')
                speaker = seg.get('speaker', 'Unknown')
                text = seg.get('text', '').strip()
                if not text:
                    continue
                # If the role or speaker changes, write out the current block
                if (role, speaker) != (current_role, current_speaker) and current_text:
                    f.write(f"[{current_role}] {current_speaker}: {current_text}\n")
                    current_text = ""
                current_role = role
                current_speaker = speaker
                # Append text
                if current_text:
                    current_text += " " + text
                else:
                    current_text = text
            if current_text:
                f.write(f"[{current_role}] {current_speaker}: {current_text}\n")
        print(f"Role-based transcript saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False

# --- Main Pipeline ---

def main():
    parser = argparse.ArgumentParser(description="Generate role-based speaker transcripts from a video file")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--output", default="role_transcript.txt", help="Output transcript file path")
    parser.add_argument("--min-speakers", type=int, default=2, help="Minimum number of speakers to detect")
    parser.add_argument("--max-speakers", type=int, default=2, help="Maximum number of speakers to detect")
    
    args = parser.parse_args()
    
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
    vad_segments = cluster_speakers(embeddings, vad_segments, min_speakers=args.min_speakers, max_speakers=args.max_speakers)
    
    # Step 6: Assign Whisper transcript segments to speakers based on overlapping timestamps
    segments_with_speakers = assign_transcript_to_speakers(transcription["segments"], vad_segments)
    
    # Step 7: Assign roles based on simple heuristic (e.g. based on question counts)
    segments_with_roles = assign_roles(segments_with_speakers)
    
    # Step 8: Save the formatted transcript with role and speaker labels
    if not save_formatted_transcript(segments_with_roles, args.output):
        sys.exit(1)
    
    # Clean up temporary audio file
    os.remove(audio_path)
    print("\nProcess completed successfully!")

if __name__ == "__main__":
    main()

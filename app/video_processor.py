import os
from pydub import AudioSegment
import whisper

def convert_video_to_audio(video_path, audio_path):
    """
    Extract audio from a video file and save as a WAV file.
    Converts to mono and 16kHz sample rate.
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        video = AudioSegment.from_file(video_path)
        video = video.set_channels(1)
        video = video.set_frame_rate(16000)
        video.export(audio_path, format="wav")
        print(f"Audio extracted successfully to {audio_path}")
        return True
    except Exception as e:
        print(f"Error converting video to audio: {e}")
        return False

def transcribe_audio(audio_path, model_name="base"):
    """
    Transcribe the audio using Whisper.
    Returns the transcription result dictionary.
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

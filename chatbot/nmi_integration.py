# nmi_integration.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NMI_API_URL = os.getenv("NMI_API_URL")
NMI_API_KEY = os.getenv("NMI_API_KEY")

def process_with_nmi(file_path):
    """
    Process the audio file with the free NMI API.
    Expected API response (JSON):
      {
         "transcript": "Full transcript text",
         "diarization": [
             {"speaker": "Speaker 1", "start": 0.0, "end": 5.0},
             {"speaker": "Speaker 2", "start": 5.0, "end": 10.0},
             ...
         ]
      }
    For simplicity, we assign the full transcript to each segment.
    """
    files = {'file': open(file_path, 'rb')}
    headers = {"Authorization": f"Bearer {NMI_API_KEY}"}
    response = requests.post(NMI_API_URL, files=files, headers=headers)
    response.raise_for_status()
    data = response.json()
    transcript = data.get("transcript", "")
    diarization = data.get("diarization", [])
    transcripts = []
    for seg in diarization:
        transcripts.append({
            "speaker": seg.get("speaker", "Unknown"),
            "transcript": transcript,
            "start": seg.get("start", 0.0),
            "end": seg.get("end", 0.0)
        })
    return {"meeting_id": None, "transcripts": transcripts}  # meeting_id to be set by caller

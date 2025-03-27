import json
import os
import requests

def extract_tasks_from_text(transcript_text: str) -> list:
    """
    Use an LLM (via the Groq API) to extract action items from a meeting transcript.
    The LLM is prompted to return a JSON array of objects, each with a 'description' field.
    """
    prompt = (
        "Extract all actionable items from the following meeting transcript. "
        "Return a JSON array where each element is an object with a 'description' field.\n\n"
        f"{transcript_text}\n\n"
    )
    groq_api_key = os.getenv("GROQ_API_KEY")
    # Replace the following URL with your actual Groq API endpoint
    api_url = os.getenv("GROQ_API_URL", "https://api.groq.example.com/infer")
    
    payload = {
        "prompt": prompt,
        "temperature": 0.7,
        "model_name": "your-model-name"  # adjust as needed
    }
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        tasks = response.json()  # Expecting JSON array
        return [task['description'] for task in tasks if 'description' in task]
    except Exception as e:
        print("Error extracting tasks from transcript:", e)
        return []

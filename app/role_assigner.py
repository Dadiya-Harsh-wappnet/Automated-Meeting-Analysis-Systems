def assign_roles(segments):
    """
    Assign roles to speakers using a simple heuristic.
    In this example, the speaker with the highest number of question marks is designated as "Interviewer".
    """
    speaker_texts = {}
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        text = seg.get('text', '')
        speaker_texts[speaker] = speaker_texts.get(speaker, "") + " " + text
    question_counts = {speaker: text.count('?') for speaker, text in speaker_texts.items()}
    interviewer = max(question_counts, key=question_counts.get) if question_counts else None
    
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        if speaker == interviewer and question_counts.get(interviewer, 0) > 0:
            seg['role'] = "Interviewer"
        else:
            seg['role'] = "Interviewee"
    return segments

def save_formatted_transcript(segments, output_file):
    """
    Save the transcript in the format: [role] speaker: text
    Returns a list of transcript lines (each as a dictionary).
    """
    transcript_lines = []
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
                if (role, speaker) != (current_role, current_speaker) and current_text:
                    line = {"role": current_role, "speaker": current_speaker, "text": current_text}
                    transcript_lines.append(line)
                    f.write(f"[{current_role}] {current_speaker}: {current_text}\n")
                    current_text = ""
                current_role = role
                current_speaker = speaker
                if current_text:
                    current_text += " " + text
                else:
                    current_text = text
            if current_text:
                line = {"role": current_role, "speaker": current_speaker, "text": current_text}
                transcript_lines.append(line)
                f.write(f"[{current_role}] {current_speaker}: {current_text}\n")
        print(f"Role-based transcript saved to {output_file}")
        return transcript_lines
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return []

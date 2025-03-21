# analysis.py
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

import numpy as np

def meeting_transcript_summary(transcripts):
    """
    Computes summary statistics from a list of MeetingTranscript objects.
    Returns:
      - total transcript count
      - average duration (end_time - start_time) for transcripts having both times.
    """
    count = len(transcripts)
    durations = [t.end_time - t.start_time for t in transcripts 
                 if t.start_time is not None and t.end_time is not None]
    avg_duration = np.mean(durations) if durations else 0
    return count, avg_duration

def employee_participation_summary(participants):
    """
    Computes participation counts per user from a list of MeetingParticipant objects.
    Returns a dictionary mapping user_id to count.
    """
    participation = {}
    for mp in participants:
        participation[mp.user_id] = participation.get(mp.user_id, 0) + 1
    return participation

def generate_bar_plot(labels, values, title, filename):
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color="green")
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def generate_line_plot(x, y, title, filename):
    plt.figure(figsize=(8, 5))
    plt.plot(x, y, marker='o', color='blue')
    plt.title(title)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def generate_meeting_participation_plot(participation_dict, users_lookup, filename):
    """
    Generates a bar plot showing meeting participation per user.
    :param participation_dict: dict mapping user_id to count.
    :param users_lookup: dict mapping user_id to user name.
    """
    labels = [users_lookup[uid] for uid in participation_dict.keys()]
    values = list(participation_dict.values())
    generate_bar_plot(labels, values, "Meeting Participation by User", filename)

# app.py
import os
from flask import Flask, request, render_template, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from db import insert_transcript_lines_sqlalchemy
from chatbot_langgraph import process_chatbot_query
from transcription_integration import run_transcription_pipeline

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"wav", "mp3", "mp4", "avi", "mkv"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return redirect(url_for("chat"))

# Meeting Upload Endpoint
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(video_path)
            meeting_id = request.form.get("meeting_id")
            if not meeting_id or not meeting_id.isdigit():
                return jsonify({"error": "Invalid or missing meeting_id"}), 400
            meeting_id = int(meeting_id)
            try:
                transcript_lines = run_transcription_pipeline(
                    video_path,
                    model_size="base",
                    min_speakers=int(request.form.get("min_speakers", 2)),
                    max_speakers=int(request.form.get("max_speakers", 2)),
                    output="role_transcript.txt"
                )
                for line in transcript_lines:
                    line["meeting_id"] = meeting_id
                insert_transcript_lines_sqlalchemy(transcript_lines=transcript_lines)
                os.remove(video_path)
                return render_template("upload.html", message="File processed and stored successfully!")
            except Exception as e:
                return jsonify({"error": f"Processing failed: {str(e)}"}), 500
        else:
            return jsonify({"error": "Invalid file type"}), 400
    return render_template("upload.html")

# Chatbot Endpoint
@app.route("/chat", methods=["GET", "POST"])
def chat():
    response = ""
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        user_role = request.form.get("role", "employee")
        user_id = request.form.get("user_id", "1")
        try:
            user_id = int(user_id)
        except ValueError:
            user_id = 1
        response = process_chatbot_query(query, user_role, user_id)
    return render_template("index.html", response=response)

if __name__ == "__main__":
    app.run(debug=True)

# app.py
from flask import Flask, request, jsonify, render_template
from chatbot_llm import generate_response

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    role = request.form.get("role", "").lower()
    query = request.form.get("query", "")
    user_name = request.form.get("name", "") if role in ["employee", "hr"] else None

    if not query:
        return jsonify({"response": "Please provide a valid query."}), 400

    if role == "employee" and not user_name:
        return jsonify({"response": "Please provide your name to retrieve employee data."}), 400

    response = generate_response(query, role, user_name)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)

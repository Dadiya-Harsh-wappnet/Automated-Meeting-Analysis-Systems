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
    employee_email = request.form.get("email", "") if role == "employee" else None

    if not query or (role == "employee" and not employee_email):
        return jsonify({"response": "Please provide a valid query and, if you are an employee, your email."}), 400

    response = generate_response(query, role, employee_email)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)

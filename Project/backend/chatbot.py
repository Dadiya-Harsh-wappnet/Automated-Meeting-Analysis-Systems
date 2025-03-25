def process_chat_query(user_role, query):
    """
    Dummy chatbot logic:
      - HR: can query all data.
      - Manager: can only query their team.
      - Employee: only personal info.
    """
    # This is a stub; replace with actual query processing and permission checks.
    if user_role == "HR":
        return f"HR Chatbot: You asked '{query}'. Here’s company-wide data."
    elif user_role == "Manager":
        return f"Manager Chatbot: You asked '{query}'. Here’s data for your team."
    else:
        return f"Employee Chatbot: You asked '{query}'. Here’s your personal info."

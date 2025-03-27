"""
chatbot.py - Implements chatbot logic using LangGraph and Groq-based LLM.
This module defines the LangGraph-based processing graph.
"""

import logging
import re
from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import Graph
from db_context import retrieve_db_context

# Configure logging
logging.basicConfig(
    filename="chatbot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Groq-based LLM (key loaded from .env in a real setup)
llm = ChatGroq(
    temperature=0.7,
    model_name="llama-3.3-70b-versatile",
    groq_api_key="your_groq_api_key_here"
)

# Define chat prompt template
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "{context}"),
    ("system", "Previous Conversation:\n{chat_history}"),
    ("human", "User Query: {query}\nPlease answer using only the provided database context, without assumptions.")
])
chain = chat_prompt | llm

def truncate_to_last_sentence(text: str) -> str:
    match = re.search(r'^(.*?[.!?])\s*(?:\S+)?$', text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def generate_response_llm(
    query: str,
    role: str,
    logged_in_user: Optional[str] = None,
    conversation_session_id: Optional[str] = None
) -> str:
    """
    Generate a chatbot response using the LLM chain and database context.
    """
    greetings = {"hola", "hi", "hello", "hey"}
    if query.strip().lower() in greetings:
        return "Hi"

    db_context = retrieve_db_context(role, logged_in_user, query)
    chat_history_text = ""  # Assume empty or load previous chat history if needed.
    context = f"You are an assistant. Role: {role}. Logged In User: {logged_in_user}."
    full_context = f"{context}\nDatabase Info:\n{db_context}\nPrevious Conversation:\n{chat_history_text}"
    
    logger.info("LLM processing query for role '%s': %s", role, query)
    inputs: Dict[str, Any] = {"context": full_context, "chat_history": chat_history_text, "query": query}
    response = chain.invoke(inputs)
    response_text = response.content if hasattr(response, "content") else str(response)
    final_response = truncate_to_last_sentence(response_text)
    return final_response

# --- LangGraph Nodes for Chatbot Pipeline ---

def user_input_node(context: Dict[str, Any]) -> Dict[str, Any]:
    context["user_input"] = context.get("raw_input", "")
    context["conversation_session_id"] = context.get("conversation_session_id", None)
    return context

def role_detector_node(context: Dict[str, Any]) -> Dict[str, Any]:
    user_role = context.get("user_role", "").lower()
    context["role"] = user_role if user_role in {"employee", "manager", "hr"} else "employee"
    return context

def intent_classifier_node(context: Dict[str, Any]) -> Dict[str, Any]:
    query = context.get("user_input", "")
    if any(word.lower() in {"hola", "hi", "hello", "hey"} for word in query.split()):
        context["intent"] = "greeting"
    elif "meeting" in query.lower() or "transcript" in query.lower():
        context["intent"] = "meeting"
    elif "performance" in query.lower() or "evaluation" in query.lower():
        context["intent"] = "performance"
    else:
        context["intent"] = "general"
    return context

def greeting_response_node(context: Dict[str, Any]) -> Dict[str, Any]:
    context["response"] = "Hi"
    return context

def employee_data_node(context: Dict[str, Any]) -> Dict[str, Any]:
    context["response"] = f"Here is your data: {retrieve_db_context('employee', context.get('user_name'), context.get('user_input'))}"
    return context

def manager_data_node(context: Dict[str, Any]) -> Dict[str, Any]:
    context["response"] = f"Team Data: {retrieve_db_context('manager', context.get('user_name'), context.get('user_input'))}"
    return context

def hr_data_node(context: Dict[str, Any]) -> Dict[str, Any]:
    context["response"] = f"HR Data: {retrieve_db_context('hr', context.get('user_name'), context.get('user_input'))}"
    return context

def general_response_node(context: Dict[str, Any]) -> Dict[str, Any]:
    context["response"] = generate_response_llm(
        context["user_input"],
        context.get("role"),
        logged_in_user=context.get("user_name"),
        conversation_session_id=context.get("conversation_session_id")
    )
    return context

def build_chatbot_graph() -> Graph:
    graph = Graph()
    graph.add_node("input", user_input_node)
    graph.add_node("role", role_detector_node)
    graph.add_node("intent", intent_classifier_node)
    graph.add_node("greeting_response", greeting_response_node)
    graph.add_node("employee_data", employee_data_node)
    graph.add_node("manager_data", manager_data_node)
    graph.add_node("hr_data", hr_data_node)
    graph.add_node("general_response", general_response_node)

    def transition(context: Dict[str, Any]) -> str:
        role = context.get("role")
        intent = context.get("intent")
        if intent == "greeting":
            return "greeting_response"
        elif intent == "meeting":
            if role == "manager":
                return "manager_data"
            elif role == "hr":
                return "hr_data"
            else:
                return "employee_data"
        elif intent == "performance":
            return "employee_data" if role == "employee" else "manager_data"
        return "general_response"
    
    graph.add_conditional_edges("intent", transition, {
        "greeting_response": "greeting_response",
        "employee_data": "employee_data",
        "manager_data": "manager_data",
        "hr_data": "hr_data",
        "general_response": "general_response"
    })
    graph.set_entry_point("input")
    return graph

def generate_response(
    query: str,
    role: str,
    logged_in_user: Optional[str] = None,
    conversation_session_id: Optional[str] = None
) -> str:
    return generate_response_llm(query, role, logged_in_user, conversation_session_id)

if __name__ == "__main__":
    initial_context = {
        "raw_input": "Can you show me the latest meeting transcript for meeting 123?",
        "user_role": "manager",
        "user_name": "Alice",
        "conversation_session_id": None
    }
    chatbot_graph = build_chatbot_graph()
    final_context = chatbot_graph.run(initial_context)
    print("Chatbot Response:", final_context.get("response"))

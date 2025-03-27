import logging
import re
import os
from dotenv import load_dotenv
import spacy

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, AIMessage
from db_context import retrieve_db_context
from db_tool import (
    get_user_id_by_name, 
    get_employee_performance_by_name, 
    get_recent_meeting_transcripts,
    get_department_roster, 
    get_meeting_participants, 
    get_skill_recommendations_by_name,
    get_personal_data,
    get_all_employee_data,
    store_chat_history,
    get_chat_history_for_user
)
from langgraph.graph import Graph
from models import SessionLocal

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please check your .env file.")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Configure logging
logging.basicConfig(filename="chatbot.log", level=logging.INFO, 
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize spaCy NLP model for intent detection
nlp = spacy.load("en_core_web_sm")

# Initialize LLM chain using ChatGroq
llm = ChatGroq(
    temperature=0.7,
    model_name="llama-3.3-70b-versatile",  # Supported model name.
    groq_api_key=GROQ_API_KEY
)

# Define chat prompt template
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "{context}"),
    ("system", "Previous Conversation:\n{chat_history}"),
    ("human", "User Query: {query}\nPlease answer ONLY using the provided database information. Do not add extra details or assumptions.")
])

# Create the chain (LLM Pipeline)
chain = chat_prompt | llm

def truncate_to_last_sentence(text: str) -> str:
    match = re.search(r'^(.*?[.!?])\s*(?:\S+)?$', text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def generate_response_llm(query: str, role: str, logged_in_user: str = None) -> str:
    """
    Generates a response using the LLM for general queries, incorporating chat history from the DB.
    If the query is a simple greeting, returns 'Hi' immediately.
    """
    # Check if query is a simple greeting
    greetings = {"hola", "hi", "hello", "hey"}
    if query.strip().lower() in greetings:
        return "Hi"
    
    session = SessionLocal()
    try:
        user_id = get_user_id_by_name(logged_in_user, session) if logged_in_user else None
        chat_history = get_chat_history_for_user(int(user_id), limit=5) if user_id else []
        chat_history_text = "\n".join(chat_history)
    
        context = f"You are an assistant. Role: {role}. Logged In User: {logged_in_user}."
        db_context = retrieve_db_context(role, logged_in_user=logged_in_user, query=query)
        full_context = f"{context}\nDatabase Info:\n{db_context}\nPrevious Conversation:\n{chat_history_text}"
    
        logger.info(f"LLM processing query for role '{role}': {query}")
        inputs = {
            "context": full_context,
            "chat_history": chat_history_text,
            "query": query
        }
        response = chain.invoke(inputs)
        response_text = response.content if hasattr(response, "content") else str(response)
        final_response = truncate_to_last_sentence(response_text)
    
        # Store chat history (both user query and bot response)
        if user_id:
            store_chat_history(int(user_id), query, "user")
            store_chat_history(int(user_id), final_response, "bot")
    
        return final_response
    except Exception as e:
        logger.error(f"Error generating LLM response: {e}")
        return "I'm sorry, I encountered an error while processing your request."
    finally:
        session.close()

# --- LangGraph Nodes for Bot Pipeline ---

def user_input_node(context):
    context['user_input'] = context.get('raw_input', '')
    return context

def role_detector_node(context):
    role = context.get('user_role', '').lower()
    context['role'] = role if role in ['employee', 'manager', 'hr'] else 'employee'
    return context

def intent_classifier_node(context):
    """
    Classifies the intent of the user's input.
    It first checks for greetings, then meeting, performance, or defaults to general.
    """
    query = context.get('user_input', '')
    doc = nlp(query)
    greetings = {"hola", "hi", "hello", "hey"}
    if any(word.lower() in greetings for word in query.split()):
        context['intent'] = 'greeting'
    elif any(token.lemma_ in ['meeting', 'transcript'] for token in doc):
        context['intent'] = 'meeting'
    elif any(token.lemma_ in ['performance', 'evaluation'] for token in doc):
        context['intent'] = 'performance'
    else:
        context['intent'] = 'general'
    return context

def greeting_response_node(context):
    """
    Returns a simple greeting response.
    """
    context['response'] = "Hi"
    return context

def employee_data_node(context):
    user_id = context.get('user_id')
    context['response'] = get_personal_data(user_id) if user_id else "Employee data not available."
    return context

def manager_data_node(context):
    query = context.get('user_input', '')
    match = re.search(r"\d+", query)
    meeting_id = int(match.group()) if match else None
    context['response'] = get_recent_meeting_transcripts(meeting_id) if meeting_id else "Please provide a valid meeting ID."
    return context

def hr_data_node(context):
    context['response'] = get_all_employee_data()
    return context

def chatbot_response_node(context):
    context['response'] = generate_response_llm(
        context['user_input'], 
        context.get('role'), 
        logged_in_user=context.get('user_name')
    )
    return context

def build_chatbot_graph():
    graph = Graph()

    # Add nodes
    graph.add_node("input", user_input_node)
    graph.add_node("role", role_detector_node)
    graph.add_node("intent", intent_classifier_node)
    graph.add_node("greeting_response", greeting_response_node)
    graph.add_node("employee_data", employee_data_node)
    graph.add_node("manager_data", manager_data_node)
    graph.add_node("hr_data", hr_data_node)
    graph.add_node("general_response", chatbot_response_node)

    # Transition function based on role and intent
    def transition(context):
        role = context.get('role')
        intent = context.get('intent')
        if intent == 'greeting':
            return "greeting_response"
        elif intent == 'meeting':
            return "manager_data" if role == 'manager' else "hr_data" if role == 'hr' else "employee_data"
        elif intent == 'performance':
            return "employee_data" if role == 'employee' else "manager_data"
        return "general_response"

    graph.add_conditional_edges(
        "intent",
        transition,
        {
            "greeting_response": "greeting_response",
            "employee_data": "employee_data",
            "manager_data": "manager_data",
            "hr_data": "hr_data",
            "general_response": "general_response"
        }
    )

    graph.set_entry_point("input")
    return graph

def generate_response(query: str, role: str, logged_in_user: str = None) -> str:
    return generate_response_llm(query, role, logged_in_user)

# Uncomment below to test the chatbot independently
# if __name__ == "__main__":
#     sample_query = "Hola"
#     print(generate_response(sample_query, role="employee", logged_in_user="Alice"))

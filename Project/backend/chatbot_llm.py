# import logging
# import re
# import os
# from dotenv import load_dotenv
# import spacy

# from langchain_core.prompts import ChatPromptTemplate
# from langchain_groq import ChatGroq
# from langchain.schema import HumanMessage, AIMessage
# from db_context import retrieve_db_context
# from db_tool import (
#     get_user_id_by_name, 
#     get_employee_performance_by_name, 
#     get_recent_meeting_transcripts,
#     get_department_roster, 
#     get_meeting_participants, 
#     get_skill_recommendations_by_name,
#     get_personal_data,
#     get_all_employee_data,
#     store_chat_history,
#     get_chat_history_for_user
# )
# from langgraph.graph import Graph
# from models import SessionLocal

# # Load environment variables
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# DATABASE_URL = os.getenv("DATABASE_URL")

# if not GROQ_API_KEY:
#     raise ValueError("GROQ_API_KEY environment variable is not set. Please check your .env file.")
# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL environment variable is not set.")

# # Configure logging
# logging.basicConfig(filename="chatbot.log", level=logging.INFO, 
#                     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# # Initialize spaCy NLP model for intent detection
# nlp = spacy.load("en_core_web_sm")

# # Initialize LLM chain using ChatGroq
# llm = ChatGroq(
#     temperature=0.7,
#     model_name="llama-3.3-70b-versatile",  # Supported model name.
#     groq_api_key=GROQ_API_KEY
# )

# # Define chat prompt template
# chat_prompt = ChatPromptTemplate.from_messages([
#     ("system", "{context}"),
#     ("system", "Previous Conversation:\n{chat_history}"),
#     ("human", "User Query: {query}\nPlease answer ONLY using the provided database information. Do not add extra details or assumptions.")
# ])

# # Create the chain (LLM Pipeline)
# chain = chat_prompt | llm

# def truncate_to_last_sentence(text: str) -> str:
#     match = re.search(r'^(.*?[.!?])\s*(?:\S+)?$', text, re.DOTALL)
#     return match.group(1).strip() if match else text.strip()

# def generate_response_llm(query: str, role: str, logged_in_user: str = None, conversation_session_id: str = None) -> str:
#     """
#     Generates a response using the LLM for general queries, incorporating chat history from the DB.
#     Optionally, uses a conversation session identifier to load and store messages for that session.
#     If the query is a simple greeting, returns "Hi" immediately.
#     """
#     # Handle simple greetings
#     greetings = {"hola", "hi", "hello", "hey"}
#     if query.strip().lower() in greetings:
#         return "Hi"
    
#     session = SessionLocal()
#     try:
#         user_id = get_user_id_by_name(logged_in_user, session) if logged_in_user else None
#         # Retrieve the chat history for this conversation session (if provided)
#         chat_history = get_chat_history_for_user(int(user_id), session_id=conversation_session_id, limit=100) if user_id else []
#         chat_history_text = "\n".join(chat_history)
    
#         context = f"You are an assistant. Role: {role}. Logged In User: {logged_in_user}."
#         db_context = retrieve_db_context(role, logged_in_user=logged_in_user, query=query)
#         full_context = f"{context}\nDatabase Info:\n{db_context}\nPrevious Conversation:\n{chat_history_text}"
    
#         logger.info(f"LLM processing query for role '{role}': {query}")
#         inputs = {
#             "context": full_context,
#             "chat_history": chat_history_text,
#             "query": query
#         }
#         response = chain.invoke(inputs)
#         response_text = response.content if hasattr(response, "content") else str(response)
#         final_response = truncate_to_last_sentence(response_text)
    
#         # Store chat history (both user query and bot response) with the conversation session id
#         if user_id:
#             store_chat_history(int(user_id), query, "user", session_id=conversation_session_id)
#             store_chat_history(int(user_id), final_response, "bot", session_id=conversation_session_id)
    
#         return final_response
#     except Exception as e:
#         logger.error(f"Error generating LLM response: {e}")
#         return "I'm sorry, I encountered an error while processing your request."
#     finally:
#         session.close()

# # --- LangGraph Nodes for Bot Pipeline ---

# def user_input_node(context):
#     context['user_input'] = context.get('raw_input', '')
#     # Optionally pass conversation_session_id from context if provided by the client
#     context['conversation_session_id'] = context.get('conversation_session_id', None)
#     return context

# def role_detector_node(context):
#     role = context.get('user_role', '').lower()
#     context['role'] = role if role in ['employee', 'manager', 'hr'] else 'employee'
#     return context

# def intent_classifier_node(context):
#     """
#     Classifies the intent of the user's input.
#     Checks for greetings first, then meeting, performance, or defaults to general.
#     """
#     query = context.get('user_input', '')
#     doc = nlp(query)
#     greetings = {"hola", "hi", "hello", "hey"}
#     if any(word.lower() in greetings for word in query.split()):
#         context['intent'] = 'greeting'
#     elif any(token.lemma_ in ['meeting', 'transcript'] for token in doc):
#         context['intent'] = 'meeting'
#     elif any(token.lemma_ in ['performance', 'evaluation'] for token in doc):
#         context['intent'] = 'performance'
#     else:
#         context['intent'] = 'general'
#     return context

# def greeting_response_node(context):
#     context['response'] = "Hi"
#     return context

# def employee_data_node(context):
#     user_id = context.get('user_id')
#     context['response'] = get_personal_data(user_id) if user_id else "Employee data not available."
#     return context

# def manager_data_node(context):
#     query = context.get('user_input', '')
#     match = re.search(r"\d+", query)
#     meeting_id = int(match.group()) if match else None
#     context['response'] = get_recent_meeting_transcripts(meeting_id) if meeting_id else "Please provide a valid meeting ID."
#     return context

# def hr_data_node(context):
#     context['response'] = get_all_employee_data()
#     return context

# def chatbot_response_node(context):
#     context['response'] = generate_response_llm(
#         context['user_input'], 
#         context.get('role'), 
#         logged_in_user=context.get('user_name'),
#         conversation_session_id=context.get('conversation_session_id')
#     )
#     return context

# def build_chatbot_graph():
#     graph = Graph()

#     # Add nodes
#     graph.add_node("input", user_input_node)
#     graph.add_node("role", role_detector_node)
#     graph.add_node("intent", intent_classifier_node)
#     graph.add_node("greeting_response", greeting_response_node)
#     graph.add_node("employee_data", employee_data_node)
#     graph.add_node("manager_data", manager_data_node)
#     graph.add_node("hr_data", hr_data_node)
#     graph.add_node("general_response", chatbot_response_node)

#     # Transition function based on role and intent
#     def transition(context):
#         role = context.get('role')
#         intent = context.get('intent')
#         if intent == 'greeting':
#             return "greeting_response"
#         elif intent == 'meeting':
#             return "manager_data" if role == 'manager' else "hr_data" if role == 'hr' else "employee_data"
#         elif intent == 'performance':
#             return "employee_data" if role == 'employee' else "manager_data"
#         return "general_response"

#     graph.add_conditional_edges(
#         "intent",
#         transition,
#         {
#             "greeting_response": "greeting_response",
#             "employee_data": "employee_data",
#             "manager_data": "manager_data",
#             "hr_data": "hr_data",
#             "general_response": "general_response"
#         }
#     )

#     graph.set_entry_point("input")
#     return graph

# def generate_response(query: str, role: str, logged_in_user: str = None, conversation_session_id: str = None) -> str:
#     return generate_response_llm(query, role, logged_in_user, conversation_session_id)

# # Uncomment below to test the chatbot independently
# # if __name__ == "__main__":
# #     sample_query = "Hola"
# #     print(generate_response(sample_query, role="employee", logged_in_user="Alice", conversation_session_id="session123"))


import logging
import re
import os
from dotenv import load_dotenv
import spacy
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from db_context import retrieve_db_context
from db_tool import get_user_id_by_name, store_chat_history, get_chat_history_for_user
from langgraph.graph import Graph
from models import SessionLocal

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

logging.basicConfig(filename="chatbot.log", level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_sm")

llm = ChatGroq(
    temperature=0.7,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY
)

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "{context}"),
    ("system", "Previous Conversation:\n{chat_history}"),
    ("human", "User Query: {query}\nAnswer using only the provided database information.")
])
chain = chat_prompt | llm

def truncate_to_last_sentence(text: str) -> str:
    match = re.search(r'^(.*?[.!?])\s*(?:\\S+)?$', text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

# ---------------- Graph Nodes ----------------
def user_input_node(context):
    context['user_input'] = context.get('raw_input', '')
    context['session_id'] = context.get('session_id', None)
    return context

def role_detector_node(context):
    role = context.get('user_role', '').lower()
    context['role'] = role if role in ['employee', 'manager', 'hr'] else 'employee'
    return context

def intent_classifier_node(context):
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
    context['response'] = "Hi"
    return context

def chat_history_node(context):
    user_id = context.get('user_id')
    session_id = context.get('session_id')
    if user_id:
        history = get_chat_history_for_user(int(user_id), session_id=session_id, limit=100)
        context['chat_history'] = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in history])
    else:
        context['chat_history'] = ""
    return context

def db_context_node(context):
    user_name = context.get('user_name')
    role = context.get('role')
    query = context.get('user_input')
    db_info = retrieve_db_context(role, logged_in_user=user_name, query=query)
    context['db_context'] = db_info
    return context

def generate_response_node(context):
    user_input = context.get('user_input')
    role = context.get('role')
    user_name = context.get('user_name')
    db_context = context.get('db_context', "")
    chat_history = context.get('chat_history', "")
    
    context_str = f"You are an assistant. Role: {role}. User: {user_name}.\n"
    context_str += f"Database Info:\n{db_context}\n"
    context_str += f"Previous Conversation:\n{chat_history}\n"
    
    inputs = {"context": context_str, "chat_history": chat_history, "query": user_input}
    try:
        response = chain.invoke(inputs)
        final_response = response.content.strip() if hasattr(response, "content") else str(response).strip()
        final_response = truncate_to_last_sentence(final_response)
        context['response'] = final_response
    except Exception as e:
        logger.error(f"LLM response error: {e}")
        context['response'] = "I'm sorry, I encountered an error."
    return context

def store_history_node(context):
    session = SessionLocal()
    try:
        user_id = context.get('user_id')
        session_id = context.get('session_id')
        from db_tool import get_latest_active_session, store_chat_history
        if not session_id:
            session_id = get_latest_active_session(user_id, session=session)
            context['session_id'] = session_id
        store_chat_history(user_id, context.get('user_input'), "user", session_id=session_id, session=session)
        store_chat_history(user_id, context.get('response'), "bot", session_id=session_id, session=session)
    except Exception as e:
        logger.error(f"Error storing chat history: {e}")
    finally:
        session.close()
    return context

def build_chatbot_graph():
    graph = Graph()
    graph.add_node("input", user_input_node)
    graph.add_node("role", role_detector_node)
    graph.add_node("intent", intent_classifier_node)
    graph.add_node("chat_history", chat_history_node)
    graph.add_node("db_context", db_context_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("greeting_response", greeting_response_node)
    graph.add_node("store_history", store_history_node)
    
    def transition(ctx):
        intent = ctx.get("intent")
        if intent == "greeting":
            return "greeting_response"
        return "generate_response"
    
    graph.add_conditional_edges("intent", transition, {
        "greeting_response": "greeting_response",
        "generate_response": "generate_response"
    })
    
    # Chain generate_response to store_history
    graph.chain("generate_response", "store_history")
    
    graph.set_entry_point("input")
    return graph

def generate_response(query: str, role: str, logged_in_user: str = None, session_id: str = None) -> str:
    context = {
        "raw_input": query,
        "user_role": role,
        "user_name": logged_in_user,
        "session_id": session_id,
        "user_id": get_user_id_by_name(logged_in_user)  # Optional: pass user ID if needed
    }
    graph = build_chatbot_graph()
    final_context = graph.execute(context)
    # final_context = graph.execute(context)
    logger.info("Final context: %s", final_context)
    

    return final_context.get("response", "I'm sorry, I encountered an error.")

# import re
# import os
# from dotenv import load_dotenv
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
#     get_skill_recommendations_by_name
# )

# # Load environment variables
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise ValueError("GROQ_API_KEY environment variable is not set. Please check your .env file.")

# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL environment variable is not set.")

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def truncate_to_last_sentence(text: str) -> str:
#     match = re.search(r'^(.*?[.!?])\s*(?:\S+)?$', text, re.DOTALL)
#     if match:
#         return match.group(1).strip()
#     return text.strip()

# # Initialize ChatGroq
# llm = ChatGroq(
#     temperature=0.7,
#     model_name="llama-3.3-70b-versatile",  # Use a supported model.
#     groq_api_key=GROQ_API_KEY
# )

# # Build a ChatPromptTemplate with clear instructions.
# chat_prompt = ChatPromptTemplate.from_messages([
#     ("system", "{context}"),
#     ("system", "Previous Conversation:\n{chat_history}"),
#     ("human", "User Query: {query}\nPlease answer ONLY using the provided database information. Do not add extra details or assumptions.")
# ])

# # Simple in-memory chat message history.
# class SimpleInMemoryChatMessageHistory:
#     def __init__(self):
#         self.messages = []
#     def add_user_message(self, message: str) -> None:
#         self.messages.append(HumanMessage(content=message))
#     def add_ai_message(self, message: str) -> None:
#         self.messages.append(AIMessage(content=message))
#     def clear(self) -> None:
#         self.messages = []

# memory = SimpleInMemoryChatMessageHistory()

# # Compose the chain using the runnable syntax.
# chain = chat_prompt | llm

# import re

# def extract_meeting_id(query):
#     """Extracts meeting ID from the query if mentioned."""
#     match = re.search(r"meeting (\d+)", query, re.IGNORECASE)
#     return int(match.group(1)) if match else None

# def extract_department(query):
#     """Extracts department name from the query if mentioned."""
#     match = re.search(r"department (\w+)", query, re.IGNORECASE)
#     return match.group(1) if match else None

# def generate_response(query: str, role: str, user_name: str = None) -> str:
#     """
#     Generate a chatbot response based on the user query.
#     Prioritizes using db_tools functions for specific data retrieval before querying LLM.
#     """
#     query_lower = query.lower()
    
#     meeting_id = extract_meeting_id(query)
#     department = extract_department(query)

#     if "employee id" in query_lower or "user id" in query_lower:
#         return get_user_id_by_name(user_name) if user_name else "Please provide an employee name."
#     elif "performance" in query_lower and ("detail" in query_lower or "records" in query_lower):
#         return get_employee_performance_by_name(user_name) if user_name else "Please provide an employee name."
#     elif "recommended skills" in query_lower:
#         return get_skill_recommendations_by_name(user_name) if user_name else "Please provide an employee name."
#     elif "meeting transcript" in query_lower and "recent" in query_lower:
#         if meeting_id:
#             return get_recent_meeting_transcripts(meeting_id=meeting_id)
#         return "Please specify a meeting ID."
#     elif "department roster" in query_lower:
#         if department:
#             return get_department_roster(department=department)
#         return "Please specify a department."
#     elif "meeting participants" in query_lower:
#         if meeting_id:
#             return get_meeting_participants(meeting_id=meeting_id)
#         return "Please specify a meeting ID."

#     # Otherwise, build context for a general query.
#     context = f"You are an assistant. Role: {role}. "
#     if user_name:
#         context += f"User: {user_name}. "
    
#     db_context = retrieve_db_context(role, user_name)
#     full_context = f"{context}\nDatabase Info:\n{db_context}"

#     logger.info(f"Received query for role '{role}': {query}")
#     chat_history_text = "\n".join([msg.content for msg in memory.messages])
    
#     inputs = {
#         "context": full_context,
#         "chat_history": chat_history_text,
#         "query": query
#     }
    
#     try:
#         response = chain.invoke(inputs)
#         response_text = response.content if hasattr(response, "content") else str(response)
#         final_response = truncate_to_last_sentence(response_text)
#         logger.info(f"Generated response: {final_response}")
#         memory.add_user_message(query)
#         memory.add_ai_message(final_response)
#         return final_response
#     except Exception as e:
#         logger.error(f"Error generating response: {e}")
#         return "I'm sorry, I encountered an error while processing your request."

# def main():
#     sample_query = "How is Alice performing?"
#     print(generate_response(sample_query, role="hr", user_name="Alice Johnson"))

# if __name__ == "__main__":
#     main()

import re
import spacy
from langgraph import StateGraph, Node
from chatbot_llm import generate_response
from db_tool import get_recent_meeting_transcripts, get_personal_data, get_team_data, get_all_employee_data
from qdrant_client import QdrantClient, models

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Initialize Qdrant for context storage
qdrant_client = QdrantClient("localhost", port=6333)
qdrant_collection = "chatbot_context"
if qdrant_collection not in qdrant_client.list_collections():
    qdrant_client.create_collection(qdrant_collection, vectors_config=models.VectorParams(size=300, distance=models.Distance.COSINE))

class UserInputNode(Node):
    def run(self, context):
        context['user_input'] = context.get('raw_input', '')
        return context

class RoleDetectorNode(Node):
    def run(self, context):
        role = context.get('user_role', '').lower()
        context['role'] = role if role in ['employee', 'manager', 'hr'] else 'employee'
        return context

class IntentClassifierNode(Node):
    def run(self, context):
        query = context.get('user_input', '')
        doc = nlp(query)
        
        if any(token.lemma_ in ["meeting", "transcript"] for token in doc):
            context['intent'] = 'meeting'
        elif any(token.lemma_ in ["performance", "evaluation"] for token in doc):
            context['intent'] = 'performance'
        else:
            context['intent'] = 'general'
        
        return context

class ContextStorageNode(Node):
    def run(self, context):
        user_id = context.get("user_id")
        user_input = context.get("user_input")
        
        # Store user input in Qdrant
        qdrant_client.upsert(
            collection_name=qdrant_collection,
            points=[models.PointStruct(id=user_id, vector=[0.0] * 300, payload={"message": user_input})]
        )
        return context

class ChatbotResponseNode(Node):
    def run(self, context):
        if context.get('intent') == 'general':
            context['response'] = generate_response(context['user_input'])
        return context

class EmployeeDataNode(Node):
    def run(self, context):
        user_id = context.get('user_id')
        context['response'] = get_personal_data(user_id)
        return context

class ManagerDataNode(Node):
    def run(self, context):
        query = context.get('user_input', '')
        match = re.search(r"\d+", query)
        meeting_id = int(match.group()) if match else None
        context['response'] = get_recent_meeting_transcripts(meeting_id) if meeting_id else "Please provide a valid meeting ID."
        return context

class HRDataNode(Node):
    def run(self, context):
        context['response'] = get_all_employee_data()
        return context

class ResponseAggregatorNode(Node):
    def run(self, context):
        return context

def build_chatbot_graph():
    graph = StateGraph()
    graph.add_node(UserInputNode(), name="input")
    graph.add_node(RoleDetectorNode(), name="role")
    graph.add_node(IntentClassifierNode(), name="intent")
    graph.add_node(ContextStorageNode(), name="context_storage")
    graph.add_node(ChatbotResponseNode(), name="general_response")
    graph.add_node(EmployeeDataNode(), name="employee_data")
    graph.add_node(ManagerDataNode(), name="manager_data")
    graph.add_node(HRDataNode(), name="hr_data")
    graph.add_node(ResponseAggregatorNode(), name="aggregate")
    
    def transition(context):
        role = context.get('role')
        intent = context.get('intent')
        
        if intent == 'meeting':
            return "manager_data" if role == 'manager' else "employee_data" if role == 'employee' else "hr_data"
        elif intent == 'performance':
            return "employee_data" if role == 'employee' else "manager_data"
        return "general_response"
    
    graph.set_transition("intent", transition)
    graph.set_start_node("input")
    return graph

def process_query_with_langgraph(raw_input, user_role, user_id):
    context = {
        "raw_input": raw_input,
        "user_role": user_role,
        "user_id": user_id
    }
    graph = build_chatbot_graph()
    final_context = graph.run(context)
    return final_context.get("response")

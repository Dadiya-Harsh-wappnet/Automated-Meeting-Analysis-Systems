import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from langchain.schema import HumanMessage, AIMessage

# Define a simple in-memory chat message history if not provided by LangChain.
class SimpleInMemoryChatMessageHistory:
    def __init__(self):
        self.messages = []

    def add_user_message(self, message: str) -> None:
        self.messages.append(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        self.messages.append(AIMessage(content=message))

    def clear(self) -> None:
        self.messages = []

# Load environment variables from .env file
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please check your .env file.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ChatGroq with the API key and a supported model.
llm = ChatGroq(
    temperature=0.7,
    model_name="llama-3.3-70b-versatile",  # Updated to a supported model.
    groq_api_key=GROQ_API_KEY,
    max_tokens=100 # Adjusted max tokens for response length.
)

# Build a ChatPromptTemplate using system and human messages.
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "{context}"),
    ("system", "Previous Conversation:\n{chat_history}"),
    ("human", "User Query: {query}\nAnswer in a clear and conversational tone:")
])

# Use our simple in-memory chat message history.
memory = SimpleInMemoryChatMessageHistory()

# Compose the chain using the runnable syntax: prompt | llm.
chain = chat_prompt | llm

def generate_response(query: str, role: str, employee_email: str = None) -> str:
    """
    Generate a ChatGPT-like response using ChatGroq integrated with LangChain and custom memory.
    
    :param query: The user's query.
    :param role: Role of the user ("employee", "manager", or "hr").
    :param employee_email: (Optional) Employee's email if role is "employee".
    :return: Generated response string.
    """
    # Build role-specific context.
    if role.lower() == "employee":
        context = (
            f"You are an assistant for employees. The employee's email is {employee_email}. "
            "Provide only information relevant to this employee and keep other data private."
        )
    elif role.lower() == "manager":
        context = (
            "You are an assistant for managers. Provide insights regarding meeting performance, transcript analysis, and team metrics."
        )
    elif role.lower() == "hr":
        context = (
            "You are an HR assistant. Provide comprehensive details regarding employee performance, meeting participation, and transcript summaries."
        )
    else:
        context = "You are a helpful assistant."

    # Log the incoming query.
    logger.info(f"Received query for role '{role}': {query}")
    
    # Retrieve the chat history as a single string.
    chat_history_text = "\n".join([msg.content for msg in memory.messages])
    
    # Build input payload.
    inputs = {
        "context": context,
        "chat_history": chat_history_text,
        "query": query
    }
    
    try:
        # Invoke the chain and capture the response.
        response = chain.invoke(inputs)
        
        # Check if response has a 'content' attribute.
        if hasattr(response, "content"):
            response_text = response.content
        elif isinstance(response, dict):
            response_text = response.get("content", "")
        else:
            response_text = str(response)
        
        # Log the generated response.
        logger.info(f"Generated response: {response_text}")
        
        # Update memory with the human and AI messages.
        memory.add_user_message(query)
        memory.add_ai_message(response_text)
        
        return response_text
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I'm sorry, I encountered an error while processing your request."

if __name__ == "__main__":
    # Sample usage for testing:
    sample_query = "How is the work-life balance at our company?"
    print(generate_response(sample_query, role="employee", employee_email="john.doe@example.com"))

import re
from chatbot_llm import generate_response
from db import get_recent_meeting_transcripts, get_personal_data, get_team_data, get_all_employee_data

# Instead of a top-level import, we perform a local import in our function.
def build_chatbot_state_machine():
    from langgraph.graph import StateGraph, Node  # local import to avoid circular dependency
    graph = StateGraph()
    
    # Define node classes as before (using the imported Node)
    class UserInputNode(Node):
        def run(self, context):
            context['user_input'] = context.get('raw_input', '')
            return context

    class RoleDetectorNode(Node):
        def run(self, context):
            role = context.get('user_role', '').lower()
            if role not in ['employee', 'manager', 'hr']:
                context['role'] = 'employee'
            else:
                context['role'] = role
            return context

    class IntentClassifierNode(Node):
        def run(self, context):
            query = context.get('user_input', '')
            if re.search(r"meeting\s*(\d+)", query, re.IGNORECASE):
                context['intent'] = 'meeting'
            else:
                context['intent'] = 'general'
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
            match = re.search(r"meeting\s*(\d+)", query, re.IGNORECASE)
            if match:
                meeting_id = int(match.group(1))
                context['response'] = get_recent_meeting_transcripts(meeting_id)
            else:
                manager_id = context.get('user_id')
                context['response'] = get_team_data(manager_id)
            return context

    class HRDataNode(Node):
        def run(self, context):
            context['response'] = get_all_employee_data()
            return context

    class ResponseAggregatorNode(Node):
        def run(self, context):
            return context

    # Add nodes to the graph.
    graph.add_node("input", UserInputNode())
    graph.add_node("role", RoleDetectorNode())
    graph.add_node("intent", IntentClassifierNode())
    graph.add_node("general", ChatbotResponseNode())
    graph.add_node("employee", EmployeeDataNode())
    graph.add_node("manager", ManagerDataNode())
    graph.add_node("hr", HRDataNode())
    graph.add_node("aggregate", ResponseAggregatorNode())
    
    # Connect nodes in sequence.
    graph.add_edge("input", "role")
    graph.add_edge("role", "intent")
    
    # Define dynamic routing based on intent and role.
    def transition(context):
        if context.get('intent') == 'meeting':
            role = context.get('role')
            if role == 'employee':
                return "employee"
            elif role == 'manager':
                return "manager"
            elif role == 'hr':
                return "hr"
        else:
            return "general"
    
    graph.add_conditional_edges("intent", transition, {
        "employee": "employee",
        "manager": "manager",
        "hr": "hr",
        "general": "general"
    })
    
    # Connect role-based or general node to the aggregator.
    graph.add_edge("employee", "aggregate")
    graph.add_edge("manager", "aggregate")
    graph.add_edge("hr", "aggregate")
    graph.add_edge("general", "aggregate")
    
    # Set the entry point.
    graph.set_entry_point("input")
    
    return graph

def process_chatbot_query(raw_input, user_role, user_id):
    context = {
        "raw_input": raw_input,
        "user_role": user_role,
        "user_id": user_id
    }
    graph = build_chatbot_state_machine()
    final_context = graph.invoke(context)
    return final_context.get("response")

# if __name__ == "__main__":
#     # Example test:
#     query = "Show me transcript for meeting 123"
#     role = "manager"
#     user_id = 42
#     response = process_chatbot_query(query, role, user_id)
#     print("Final Response:", response)

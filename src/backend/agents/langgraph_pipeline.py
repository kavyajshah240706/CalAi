from langgraph.graph import StateGraph, END
from src.backend.agents.schema import GraphState
from src.backend.agents.node1_nlp import node1_nlp_parser
from src.backend.agents.node2_data import node2_data_retrieval
from src.backend.agents.node3_math import node3_math_engine
from src.backend.agents.node4_recommender import node4_recommender

def build_nutrition_graph():
    """
    Builds the 4-node LangGraph sequential pipeline.
    """
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("nlp_parser", node1_nlp_parser)
    workflow.add_node("data_retrieval", node2_data_retrieval)
    workflow.add_node("math_engine", node3_math_engine)
    workflow.add_node("recommender", node4_recommender)
    
    # Add edges
    workflow.set_entry_point("nlp_parser")
    workflow.add_edge("nlp_parser", "data_retrieval")
    workflow.add_edge("data_retrieval", "math_engine")
    workflow.add_edge("math_engine", "recommender")
    workflow.add_edge("recommender", END)
    
    # Compile
    app = workflow.compile()
    return app

# Singleton compiled graph
nutrition_graph = build_nutrition_graph()

def run_pipeline(user_input: str) -> dict:
    """
    Helper function to execute the graph with a given user input.
    """
    initial_state = GraphState(user_input=user_input)
    # The output is the final state dictionary
    result = nutrition_graph.invoke(initial_state.model_dump())
    return result

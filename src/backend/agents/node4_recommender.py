from src.backend.agents.schema import GraphState
from src.backend.agents.node2_data import get_firecrawl_context
from google import genai
from google.genai import types
import os

def node4_recommender(state: GraphState) -> GraphState:
    """
    Node 4: Agentic Nutrient Recommender
    Evaluates the macro ratios and suggests localized ingredient additions to balance it out,
    using Firecrawl and Google Search dynamically.
    """
    if not state.calculated_nutrition:
        return state
        
    client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="global")
    
    system_prompt = f"""You are an elite clinical sports nutritionist. Analyze the calculated meal macros: 
    {state.calculated_nutrition}. 
    
    Determine if it is deficient in protein, fats, or carbohydrates based on standard nutritional balance guidelines. 
    If it is deficient, recommend a complementary food item native to the cuisine to optimize the macronutrient profile. 
    You have access to get_firecrawl_context and google_search to look up local cultural recipes or specific nutritional values of your recommendations before suggesting them.
    Keep it highly actionable, concise, and friendly."""
    
    try:
        chat = client.chats.create(
            model="gemini-3.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                tools=[get_firecrawl_context, {"google_search": {}}]
            )
        )
        
        response = chat.send_message("Please provide your recommendation based on these macros. Use your tools if you need to look up specific ingredients.")
        state.recommendations = response.text.strip()
    except Exception as e:
        print(f"Node 4 Agentic Error: {e}")
        state.recommendations = "Consider adding a lean protein source or fiber-rich vegetable to balance this meal."
        
    return state

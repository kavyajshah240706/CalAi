from src.backend.agents.schema import GraphState
from google import genai
from google.genai import types
import os

def node4_recommender(state: GraphState) -> GraphState:
    """
    Node 4: Nutrient Recommender Agent
    Evaluates the macro ratios and suggests localized ingredient additions to balance it out.
    """
    if not state.calculated_nutrition:
        return state
        
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
        http_options=types.HttpOptions(api_version="v1")
    )
    
    system_prompt = f"""You are a clinical sports nutritionist. Analyze the calculated meal macros: 
    {state.calculated_nutrition}. 
    
    Determine if it is deficient in protein, fats, or carbohydrates based on standard nutritional balance guidelines. 
    If it is deficient (e.g., protein < 15-20g for a main meal), recommend a complementary food item native to the cuisine 
    (e.g., adding 100g of paneer or tofu to a low-protein Indian meal) to optimize the macronutrient profile. 
    Keep it highly actionable, concise, and friendly."""
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Please provide your recommendation based on these macros.",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            tools=[{"google_search": {}}]
        )
    )
    
    state.recommendations = response.text.strip()
    
    return state

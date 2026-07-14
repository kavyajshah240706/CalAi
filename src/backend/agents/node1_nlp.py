from src.backend.agents.schema import GraphState
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import os

class ParsedQuerySchema(BaseModel):
    food_name: str = Field(description="The name of the food item")
    quantity: float = Field(description="The estimated volume in milliliters. Must be a realistic serving size (typically 100-600 ml for a single plate).")
    unit: str = Field(description="The unit of measurement. MUST always be 'ml'.")
    state: str = Field(description="The state or texture of the food (e.g., raw, cooked, pureed, solid)")

def node1_nlp_parser(state: GraphState) -> GraphState:
    """
    Node 1: NLP Parsing Agent with Gemini 2.5 Pro Volume Sanity Check.
    Uses Gemini Vision to identify the food and validate the volume estimate.
    """
    user_input = state.user_input
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
        http_options=types.HttpOptions(api_version="v1")
    )
    
    prompt_text = f"""You are an expert food identification and portion estimation AI.

TASK: Identify the food in the image/text and estimate a realistic serving volume in milliliters.

INPUT: {user_input}

CRITICAL VOLUME SANITY CHECK:
The input may contain a volume estimate from a depth-estimation model. This estimate is often WILDLY INACCURATE.
You MUST apply your own judgement based on the image:
- A typical single plate of curry, rice, pasta, etc. is 250-450 ml.
- A bowl of soup or dal is 200-350 ml.
- A sandwich or burger is equivalent to about 200-350 ml in volume.
- A small snack (samosa, cookie) is 50-150 ml.
- A glass of juice/milk is 200-300 ml.

If the depth model's estimate seems absurd (e.g., less than 10 ml or more than 2000 ml for a normal plate),
IGNORE it completely and use your own visual estimate based on the guidelines above.

Output the food_name, a realistic quantity in ml, unit as 'ml', and the state (cooked/raw/etc).
"""
    
    contents = [prompt_text]
    
    if state.image_base64:
        import base64
        image_bytes = base64.b64decode(state.image_base64)
        contents = [
            prompt_text,
            types.Part.from_bytes(data=image_bytes, mime_type='image/png')
        ]
    
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ParsedQuerySchema,
            temperature=0.1,
            tools=[{"google_search": {}}]
        )
    )
    
    try:
        result = json.loads(response.text)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        result = {}
        
    # Final safety clamp: ensure volume is within sane bounds
    quantity = float(result.get("quantity", 300))
    if quantity < 20:
        quantity = 250.0  # Default to a reasonable serving
    elif quantity > 2000:
        quantity = 400.0  # Cap absurdly large estimates
        
    state.parsed_query = {
        "food_name": result.get("food_name", ""),
        "quantity": quantity,
        "unit": "ml",
        "state": result.get("state", "")
    }
    
    return state

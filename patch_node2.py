import re

with open("src/backend/agents/node2_data.py", "r") as f:
    content = f.read()

# 1. Add docstrings to the tools
rag_func = """def get_rag_context(food_name: str) -> str:
    \"\"\"Queries the internal specialized RAG database to find density and macronutrient information for a specific food. Call this first for packaged or rare foods.\"\"\"
"""
content = re.sub(r'def get_rag_context\(food_name: str\) -> str:\n', rag_func, content)

web_func = """def get_firecrawl_context(food_name: str) -> str:
    \"\"\"Searches the live internet to find general macronutrient information (calories, protein, carbs, fats) for a food. Call this if the RAG database lacks sufficient information.\"\"\"
"""
content = re.sub(r'def get_firecrawl_context\(food_name: str\) -> str:\n', web_func, content)

# 2. Replace node2_data_retrieval
new_node2 = """def node2_data_retrieval(state: GraphState) -> GraphState:
    \"\"\"
    Node 2: Agentic Data Retrieval
    An LLM Agent dynamically decides whether to query the DB, RAG, or Web Search.
    \"\"\"
    pq = state.parsed_query
    if not pq: return state
        
    food_name = pq.get("food_name")
    
    # 1. Try Fast DB Lookup
    db_macros = get_food_macros(food_name)
    if db_macros:
        state.profile = db_macros
        return state
        
    # 2. Agentic RAG & Web Search Loop
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
        http_options=types.HttpOptions(api_version="v1")
    )
    
    prompt = f\"\"\"
    You are a clinical nutrition extraction agent. Your goal is to find the macronutrients and density for '{food_name}'.
    You have access to two tools:
    1. get_rag_context: Searches our internal clinical database.
    2. get_firecrawl_context: Searches the live web.
    
    You MUST use these tools to gather information. You can use both if needed.
    Once you have enough information, synthesize it and return EXACTLY a valid JSON object with these exact keys:
    "density_g_ml", "kcal_per_100g", "protein_per_100g", "carbs_per_100g", "fats_per_100g".
    Do not return any markdown formatting or extra text.
    \"\"\"
    
    try:
        # Initialize the Chat Session with Automatic Function Calling
        # The SDK will automatically execute the Python functions and feed the results back!
        chat = client.chats.create(
            model="gemini-3.5-flash",
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=[get_rag_context, get_firecrawl_context]
            )
        )
        
        response = chat.send_message(prompt)
        content = response.text
        
        # Handle list response from newer multimodal models
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    content = item.get("text", "")
                    break
            if isinstance(content, list):
                content = str(content)
                
        content = content.strip()
        
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        content = content.strip()
            
        proxy_macros = json.loads(content)
        proxy_macros["food_name"] = food_name
        proxy_macros["source"] = "Agentic RAG"
        state.profile = proxy_macros
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini JSON: {e}, raw content: {content[:200]}")
        state.profile = {
            "food_name": food_name,
            "density_g_ml": 1.0,
            "kcal_per_100g": 100, "protein_per_100g": 5, "carbs_per_100g": 10, "fats_per_100g": 5,
            "source": "Emergency Fallback"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in Node 2 Agentic call: {e}")
        state.profile = {
            "food_name": food_name,
            "density_g_ml": 1.0,
            "kcal_per_100g": 100, "protein_per_100g": 5, "carbs_per_100g": 10, "fats_per_100g": 5,
            "source": "Emergency Fallback"
        }
        
    return state
"""

# Replace the entire node2_data_retrieval function
content = re.sub(r'def node2_data_retrieval\(state: GraphState\) -> GraphState:.*', new_node2, content, flags=re.DOTALL)

with open("src/backend/agents/node2_data.py", "w") as f:
    f.write(content)

print("Agentic RAG Patched!")

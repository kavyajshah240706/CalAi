from src.backend.agents.schema import GraphState
from src.backend.database.db_client import get_food_macros
from google import genai
from google.genai import types
from langchain_postgres import PGVector
import os
import json

class GenAIEmbeddingsWrapper:
    def __init__(self, model_name="text-embedding-004"):
        self.model_name = model_name
        self.client = genai.Client(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            http_options=types.HttpOptions(api_version="v1")
        )
        
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=texts
        )
        return [emb.values for emb in response.embeddings]
        
    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=text
        )
        return response.embeddings[0].values

def get_rag_context(food_name: str) -> str:
    try:
        db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
            
        embeddings = GenAIEmbeddingsWrapper(model_name="text-embedding-004")
        vectorstore = PGVector(
            embeddings=embeddings,
            collection_name="food_density_rag_v2",
            connection=db_url,
            use_jsonb=True,
        )
        docs = vectorstore.similarity_search(f"{food_name} density and macronutrients", k=3)
        return "\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"RAG Error: {e}")
        return ""

def get_firecrawl_context(food_name: str) -> str:
    try:
        from firecrawl import FirecrawlApp
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if not api_key: return ""
        app = FirecrawlApp(api_key=api_key)
        # We query the web for the macros
        res = app.search(f"{food_name} nutritional value calories protein carbs fat per 100g")
        if res and isinstance(res, dict) and "data" in res:
            chunks = [item.get("content", item.get("markdown", "")) for item in res["data"]]
            return "\n\n".join(chunks[:2])
    except Exception as e:
        print(f"Firecrawl Error: {e}")
    return ""

def node2_data_retrieval(state: GraphState) -> GraphState:
    """
    Node 2: Data Retrieval & Proxy Agent
    Checks DB -> RAG (PDF) -> Web Search (Firecrawl) -> Gemini Proxy
    """
    pq = state.parsed_query
    if not pq: return state
        
    food_name = pq.get("food_name")
    
    # 1. Try DB Lookup
    db_macros = get_food_macros(food_name)
    if db_macros:
        state.profile = db_macros
        return state
        
    # 2. Try RAG
    rag_context = get_rag_context(food_name)
    
    # 3. Try Firecrawl if RAG context is empty
    web_context = ""
    if not rag_context.strip():
        web_context = get_firecrawl_context(food_name)
        
    # 4. Proxy/Synthesize using Gemini
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
        http_options=types.HttpOptions(api_version="v1")
    )
    
    prompt = f"""
    You are a clinical nutrition extraction agent.
    The food '{food_name}' (State: {pq.get('state')}) was not found in the primary database.
    
    Here is context retrieved from our internal Density PDF Database:
    {rag_context}
    
    Here is context retrieved from a live web search:
    {web_context}
    
    Based ONLY on the provided context (prioritize PDF, then Web), extract the macros.
    If the context is entirely useless, act as a proxy agent:
    1. Assign a Master Texture Density (e.g. Thick Puree = 1.10 g/ml).
    2. Provide the estimated macronutrient distribution per 100g.
    
    Return EXACTLY a valid JSON object with these exact keys:
    "density_g_ml", "kcal_per_100g", "protein_per_100g", "carbs_per_100g", "fats_per_100g".
    Do not return any markdown formatting or extra text.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=[{"google_search": {}}]
            )
        )
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
        proxy_macros["source"] = "RAG" if rag_context.strip() else ("Web" if web_context else "Proxy")
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
        print(f"Error in Node 2 Gemini call: {e}")
        state.profile = {
            "food_name": food_name,
            "density_g_ml": 1.0,
            "kcal_per_100g": 100, "protein_per_100g": 5, "carbs_per_100g": 10, "fats_per_100g": 5,
            "source": "Emergency Fallback"
        }
        
    return state

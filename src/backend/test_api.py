import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def test_api():
    print("Testing Gemini API Key...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("NO API KEY FOUND in .env!")
        return

    print("\n--- Testing Embedding Model: text-embedding-004 ---")
    try:
        client = genai.Client(http_options=types.HttpOptions(api_version="v1"))
        response = client.models.embed_content(
            model="text-embedding-004",
            contents="Hello world"
        )
        vector = response.embeddings[0].values
        print(f"SUCCESS! Embedded 'Hello world' into {len(vector)} dimensions.")
    except Exception as e:
        print(f"FAILED Embeddings: {e}")

    print("\n--- Testing Chat Model: gemini-3.5-flash ---")
    try:
        client = genai.Client(http_options=types.HttpOptions(api_version="v1"))
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents="Say the word 'Nutrition'",
            config=types.GenerateContentConfig(temperature=0)
        )
        print(f"SUCCESS! Model gemini-3.5-flash responded with: {response.text}")
    except Exception as e:
        print(f"FAILED Chat Model: {e}")

if __name__ == "__main__":
    test_api()

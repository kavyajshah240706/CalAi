import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from google.genai import types
from langchain_postgres import PGVector
from dotenv import load_dotenv

class GenAIEmbeddingsWrapper:
    def __init__(self, model_name="text-embedding-004"):
        self.model_name = model_name
        self.client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1")
        
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

load_dotenv()

def ingest_pdf(pdf_path: str):
    print(f"Loading {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)
    
    print(f"Created {len(chunks)} chunks. Connecting to pgvector...")
    
    embeddings = GenAIEmbeddingsWrapper(model_name="text-embedding-004")
    # For langchain_postgres, we typically need a psycopg connection string (psycopg 3)
    # The format is postgresql+psycopg://...
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
        
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name="food_density_rag_v2",
        connection=db_url,
        use_jsonb=True,
    )
    
    print("Adding documents to vector store in batches...")
    batch_size = 15
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Adding batch {i//batch_size + 1} ({len(batch)} chunks)...")
        vectorstore.add_documents(batch)
    print("Ingestion complete!")

if __name__ == "__main__":
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "density_DB_v2_0_01.pdf"))
    if os.path.exists(pdf_path):
        ingest_pdf(pdf_path)
    else:
        print(f"PDF not found at {pdf_path}")

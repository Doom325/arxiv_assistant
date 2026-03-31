import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.llm_service import llm_service
from config import settings

def test_embedding():
    print(f"Testing embedding with provider: {settings.AI_PROVIDER}")
    print(f"Model: {settings.OLLAMA_EMBEDDING_MODEL}")
    
    text = "This is a test sentence for EmbeddingGemma."
    try:
        embedding = llm_service.generate_embedding(text)
        print(f"Success! Generated embedding of length: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_embedding()

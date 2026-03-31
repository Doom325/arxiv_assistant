import ollama

model = "embeddinggemma"
text = "This is a test sentence for EmbeddingGemma."

print(f"Generating embedding for model: {model}...")
try:
    response = ollama.embeddings(model=model, prompt=text)
    embedding = response["embedding"]
    
    print("Success!")
    print(f"Embedding length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
except Exception as e:
    print(f"Error: {e}")

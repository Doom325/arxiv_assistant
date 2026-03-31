from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

model_id = "google/embeddinggemma-300m"

print(f"Loading model: {model_id}...")
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModel.from_pretrained(model_id, trust_remote_code=True)

sentences = ["This is a test sentence for EmbeddingGemma."]

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

print("Generating embeddings...")
encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

with torch.no_grad():
    model_output = model(**encoded_input)

# Perform pooling
sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

# Normalize embeddings
sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

print("Success!")
print(f"Embedding shape: {sentence_embeddings.shape}")
print(f"First 5 values: {sentence_embeddings[0][:5].tolist()}")

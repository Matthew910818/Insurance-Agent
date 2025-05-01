# embeddings.py
import os
from sentence_transformers import SentenceTransformer
# Define a path to store/download the model manually
MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "models/bge-small")
# Load model (will load from local folder if exists)
model = SentenceTransformer(MODEL_PATH)

def get_embedding(texts: list[str]):
    if isinstance(texts, str):
        texts = [texts]
    return model.encode(texts, normalize_embeddings=True)  

# Create a ChromaDB-compatible embedding function class
class BGEEmbeddingFunction:
    def __call__(self, input: list[str]) -> list[list[float]]:
        return get_embedding(input)

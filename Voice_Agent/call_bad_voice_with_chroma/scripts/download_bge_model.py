# scripts/download_bge_model.py

from sentence_transformers import SentenceTransformer

print("🔻 Downloading BGE-small to ./models/bge-small")
SentenceTransformer("BAAI/bge-small-en-v1.5").save("./models/bge-small")
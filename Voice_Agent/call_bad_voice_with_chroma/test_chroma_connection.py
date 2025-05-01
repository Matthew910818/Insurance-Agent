import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

print("Connecting to Chroma...")
client = chromadb.HttpClient(host="localhost", port=8001)

print("Creating collection...")
collection = client.get_or_create_collection(name="test_collection")

print("Adding document...")
collection.add(
    documents=["This is a test document"],
    metadatas=[{"source": "test"}],
    ids=["test1"]
)

print("Querying document...")
results = collection.query(
    query_texts=["test document"],
    n_results=1
)

print("Results:", results) 
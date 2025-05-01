#!/usr/bin/env python3
import os
import sys
import json
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

def connect_to_chroma():
    CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
    
    print(f"🔄 Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
    
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT
    )
    return client

def cleanup_collection(collection):
    print(f"\n🔍 Checking collection...")
    
    # Get all records
    results = collection.get()
    if not results or not results.get('ids'):
        print("No records found.")
        return
    
    print(f"Found {len(results['ids'])} records")
    
    # Track records to delete
    to_delete = []
    
    for i, (id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
        print(f"\nChecking record {i+1}/{len(results['ids'])}")
        print(f"ID: {id}")
        print(f"Metadata: {json.dumps(metadata, indent=2)}")
        
        should_delete = input("\nDelete this record? (y/n/q to quit): ").lower()
        if should_delete == 'q':
            break
        if should_delete == 'y':
            to_delete.append(id)
    
    # Delete selected records
    if to_delete:
        print(f"\n🗑️ Deleting {len(to_delete)} records...")
        collection.delete(ids=to_delete)
        print("✅ Deletion complete")
    else:
        print("\nNo records selected for deletion")

def main():
    try:
        client = connect_to_chroma()
        
        # Get students collection
        students = client.get_collection("students")
        print("\n📚 Processing students collection...")
        cleanup_collection(students)
        
        # Get jobs collection
        jobs = client.get_collection("jobs")
        print("\n💼 Processing jobs collection...")
        cleanup_collection(jobs)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
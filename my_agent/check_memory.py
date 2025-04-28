#!/usr/bin/env python3
"""
A simple utility to check the status of your memory system and create a test memory
if needed to verify everything is working properly.
"""
import os
import sys
import json
import datetime
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

def check_qdrant_status():
    """Check if Qdrant is accessible and properly configured."""
    print("\n" + "="*80)
    print("CHECKING MEMORY SYSTEM STATUS")
    print("="*80)
    
    # Check OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ ERROR: OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
        return False
    
    print(f"✓ OpenAI API key found: {openai_api_key[:4]}...{openai_api_key[-4:]}")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
    print("✓ OpenAI embeddings initialized")
    
    # Check Qdrant database
    try:
        print("\nTrying to connect to local Qdrant database...")
        client = QdrantClient(path="./qdrant_db")
        print("✓ Connected to local Qdrant database")
        
        # Check collections
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"✓ Found collections: {collection_names}")
        
        research_collection_exists = "insurance_research" in collection_names
        
        if research_collection_exists:
            count = client.count("insurance_research")
            print(f"✓ Collection 'insurance_research' has {count.count} points")
        else:
            print("❌ Collection 'insurance_research' not found")
            
            # Ask if we should create it
            create_collection = input("Would you like to create the collection? (y/n): ")
            if create_collection.lower() == 'y':
                client.recreate_collection(
                    collection_name="insurance_research",
                    vectors_config={"size": 1536, "distance": "Cosine"}
                )
                print("✓ Created 'insurance_research' collection")
                research_collection_exists = True
        
        return research_collection_exists
        
    except Exception as e:
        print(f"❌ ERROR accessing Qdrant database: {e}")
        print("This could mean Qdrant is already in use by another process.")
        return False

def create_test_memory():
    """Create a test memory to verify the system works."""
    print("\n" + "="*80)
    print("CREATING TEST MEMORY")
    print("="*80)
    
    try:
        # Initialize everything
        openai_api_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        client = QdrantClient(path="./qdrant_db")
        vectorstore = Qdrant(
            client=client,
            collection_name="insurance_research",
            embeddings=embeddings,
        )
        
        # Create a test memory
        doc_id = str(uuid.uuid4())
        test_memory = Document(
            page_content="""
            This is a test memory entry to verify the memory system is working.
            Customer had a claim denied for an MRI procedure (CPT code 70553).
            The denial reason was that the procedure required prior authorization.
            Patient believes this was in error as they did receive authorization.
            The policy number is ABC123456 with ID #78901.
            """,
            metadata={
                "source": "test_memory",
                "timestamp": datetime.datetime.now().isoformat(),
                "id": doc_id
            }
        )
        
        # Add to vector store
        vectorstore.add_documents([test_memory])
        print(f"✓ Created test memory with ID: {doc_id}")
        
        # Verify we can retrieve it
        results = vectorstore.similarity_search("claim denial MRI authorization", k=1)
        if results:
            print("✓ Successfully retrieved test memory")
            print(f"Content: {results[0].page_content.strip()}")
        else:
            print("❌ Could not retrieve the test memory")
            
    except Exception as e:
        import traceback
        print(f"❌ ERROR creating test memory: {e}")
        print(traceback.format_exc())

def search_for_memories(query):
    """Search for memories with the given query."""
    print("\n" + "="*80)
    print(f"SEARCHING MEMORIES FOR: '{query}'")
    print("="*80)
    
    try:
        # Initialize everything
        openai_api_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        client = QdrantClient(path="./qdrant_db")
        vectorstore = Qdrant(
            client=client,
            collection_name="insurance_research",
            embeddings=embeddings,
        )
        
        # Search for memories
        results = vectorstore.similarity_search_with_score(query, k=5)
        
        # Format and display the results
        if not results:
            print("No memories found matching your query.")
        else:
            print(f"Found {len(results)} memories:")
            for i, (doc, score) in enumerate(results, 1):
                print(f"\n--- MEMORY #{i} (Relevance: {score:.4f}) ---")
                print(f"Content: {doc.page_content.strip()}")
                print(f"Source: {doc.metadata.get('source', 'unknown')}")
                if 'timestamp' in doc.metadata:
                    print(f"Timestamp: {doc.metadata['timestamp']}")
                    
    except Exception as e:
        import traceback
        print(f"❌ ERROR searching memories: {e}")
        print(traceback.format_exc())

def main():
    """Main function to run the memory check utility."""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Check and test memory system in LangGraph.')
    parser.add_argument('--create-test', '-c', action='store_true', help='Create a test memory')
    parser.add_argument('--search', '-s', type=str, help='Search query for memories')
    args = parser.parse_args()
    
    # Check Qdrant status
    qdrant_ok = check_qdrant_status()
    
    if args.create_test and qdrant_ok:
        create_test_memory()
    
    if args.search and qdrant_ok:
        search_for_memories(args.search)
        
    if not args.create_test and not args.search:
        print("\nTo create a test memory: python check_memory.py --create-test")
        print("To search memories: python check_memory.py --search \"your query here\"")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main() 
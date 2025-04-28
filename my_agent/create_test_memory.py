#!/usr/bin/env python3
"""
Quick script to add a test memory to the API database
"""
import os
import sys
import datetime
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

def create_test_memory():
    """Create a test memory in the API database."""
    
    # Path to the API database
    api_db_path = "./qdrant_db_api"
    
    print(f"\nCreating test memory in database at {api_db_path}")
    
    try:
        # Initialize everything
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("Error: OpenAI API key not found in environment")
            return
            
        print(f"Using OpenAI API key: {openai_api_key[:4]}...{openai_api_key[-4:]}")
        
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        client = QdrantClient(path=api_db_path)
        
        # Check if collection exists, create if needed
        collections = client.get_collections()
        if not any(c.name == "insurance_research" for c in collections.collections):
            print("Creating 'insurance_research' collection")
            client.recreate_collection(
                collection_name="insurance_research",
                vectors_config={"size": 1536, "distance": "Cosine"}
            )
        
        vectorstore = Qdrant(
            client=client,
            collection_name="insurance_research",
            embeddings=embeddings,
        )
        
        # Create test memories
        memories = [
            {
                "content": """
                Customer Jane Doe had a claim denied for an MRI procedure (CPT code 70553).
                The denial reason was that the procedure required prior authorization.
                Patient provided evidence they did receive authorization.
                The policy number is ABC123456 with ID #78901.
                """,
                "metadata": {
                    "source": "email_exchange",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
                    "id": str(uuid.uuid4())
                }
            },
            {
                "content": """
                Insurance claim for surgery (CPT 27447) was denied due to "experimental procedure" designation.
                Patient John Smith appealed with evidence that the procedure is FDA approved and standard care.
                The policy specifically excludes experimental treatments under section 4.3.
                Appeal was successful and claim was paid on reconsideration.
                """,
                "metadata": {
                    "source": "email_exchange",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(days=15)).isoformat(),
                    "id": str(uuid.uuid4())
                }
            },
            {
                "content": """
                Policy exclusion for pre-existing conditions cannot be applied after 12 months of continuous coverage.
                This is according to the ACA regulations and state law in California.
                In the case with Samuel Johnson, his diabetes treatment was incorrectly denied as pre-existing
                despite having 18 months of continuous coverage with the insurer.
                """,
                "metadata": {
                    "source": "research_results",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(),
                    "id": str(uuid.uuid4())
                }
            }
        ]
        
        # Add each memory to the vector store
        for memory in memories:
            doc_id = memory["metadata"]["id"]
            document = Document(
                page_content=memory["content"].strip(),
                metadata=memory["metadata"]
            )
            
            # Add to vector store
            vectorstore.add_documents([document])
            print(f"Added memory with ID: {doc_id}")
            
        print("\nTest memories created successfully!")
        print("You can now query them with: curl 'http://localhost:8000/memories?query=denial&limit=3'")
        
    except Exception as e:
        import traceback
        print(f"Error creating test memories: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    create_test_memory() 
#!/usr/bin/env python3
"""
API endpoint to check memories.
This can be added as a custom route in LangGraph Studio.
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
import os
import shutil
import datetime
import uuid
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize vector database connection
vectorstore = None
api_db_path = "./qdrant_db_api"  # Use a separate path for the API

# Try to clone the existing database if possible
try:
    if os.path.exists("./qdrant_db") and not os.path.exists(api_db_path):
        print(f"Trying to copy database from ./qdrant_db to {api_db_path}")
        shutil.copytree("./qdrant_db", api_db_path)
        print("Database copied successfully")
except Exception as e:
    print(f"Couldn't copy database: {e}")

try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        print(f"Using OpenAI API key: {openai_api_key[:4]}...{openai_api_key[-4:]}")
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        
        # Try to connect to local Qdrant with a new connection
        client = QdrantClient(path=api_db_path)
        print(f"Connected to local Qdrant database at {api_db_path}")
        
        try:
            # Check if collection exists
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            print(f"Found collections: {collection_names}")
            
            if not "insurance_research" in collection_names:
                print("Collection 'insurance_research' not found. Creating it...")
                client.recreate_collection(
                    collection_name="insurance_research",
                    vectors_config={"size": 1536, "distance": "Cosine"}
                )
                print("Created 'insurance_research' collection")
            
            # Initialize vector store with the client
            vectorstore = Qdrant(
                client=client,
                collection_name="insurance_research",
                embeddings=embeddings,
            )
            print("Qdrant vector store initialized successfully for API")
        except Exception as e:
            print(f"Error initializing vector store: {e}")
except Exception as e:
    print(f"Failed to initialize vector database: {e}")

class MemoryResponse(BaseModel):
    memories: List[Dict[str, Any]]
    count: int
    formatted_output: Optional[str] = None
    status: str

class CreateMemoryResponse(BaseModel):
    success: bool
    message: str
    memory_ids: List[str]

@app.get("/")
async def root():
    """
    Root endpoint providing information about available routes.
    """
    db_status = "available" if vectorstore else "unavailable"
    
    return {
        "message": "Memory API is running",
        "vector_database_status": db_status,
        "available_endpoints": [
            {
                "path": "/memories",
                "description": "Get all memories or search for specific ones",
                "example": "/memories?query=denial&limit=5&formatted=true"
            },
            {
                "path": "/status",
                "description": "Check the status of the memory system",
            },
            {
                "path": "/create-test-memories",
                "description": "Create test memories in the database",
                "method": "POST"
            },
            {
                "path": "/all-memories",
                "description": "Get all memories from the database without requiring a search query",
                "method": "GET"
            }
        ]
    }

@app.get("/status")
async def status():
    """
    Return the status of the memory system and database connections.
    """
    return {
        "vector_database": {
            "available": vectorstore is not None,
            "type": f"Qdrant (local at {api_db_path})" if vectorstore else "Not connected",
            "error": None if vectorstore else "Could not initialize vector database. It may be in use by another process."
        },
        "openai_api": {
            "available": os.getenv("OPENAI_API_KEY") is not None,
        }
    }

@app.post("/create-test-memories", response_model=CreateMemoryResponse)
async def create_test_memories():
    """
    Create test memories in the database.
    """
    if not vectorstore:
        return {
            "success": False,
            "message": "Vector database not available",
            "memory_ids": []
        }
    
    try:
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
        memory_ids = []
        for memory in memories:
            doc_id = memory["metadata"]["id"]
            document = Document(
                page_content=memory["content"].strip(),
                metadata=memory["metadata"]
            )
            
            # Add to vector store
            vectorstore.add_documents([document])
            memory_ids.append(doc_id)
            
        return {
            "success": True,
            "message": f"Successfully created {len(memory_ids)} test memories",
            "memory_ids": memory_ids
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Error creating test memories: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        return {
            "success": False,
            "message": f"Error creating test memories: {str(e)}",
            "memory_ids": []
        }

@app.get("/memories", response_model=MemoryResponse)
async def get_memories(
    query: str = Query(None, description="Search query string"),
    limit: int = Query(10, description="Maximum number of results"),
    formatted: bool = Query(False, description="Return formatted memory context")
):
    """
    Retrieve memories from the vector database.
    
    Parameters:
    - query: Optional search query string
    - limit: Maximum number of results to return
    - formatted: Whether to return formatted memories as they would appear in prompts
    
    Returns:
    - List of memories matching the query
    """
    if not vectorstore:
        return {
            "memories": [],
            "count": 0,
            "formatted_output": None,
            "status": "error: vector database not available"
        }
    
    try:
        # Define search function
        def search_memory(query: str, limit: int = 3) -> List[Dict]:
            if not vectorstore:
                return []
            
            try:
                results = vectorstore.similarity_search_with_score(query, k=limit)
                
                # Format the results
                memory_results = []
                for doc, score in results:
                    memory_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance_score": float(score)
                    })
                
                return memory_results
            except Exception as e:
                print(f"Error searching memory: {e}")
                return []
                
        # Define formatting function
        def get_relevant_memories(query: str, limit: int = 5) -> str:
            import datetime
            memories = search_memory(query, limit=limit)
            
            if not memories:
                return ""
            
            # Format the memories for inclusion in prompts
            formatted_memories = "RELEVANT PAST INFORMATION:\n\n"
            for i, memory in enumerate(memories, 1):
                formatted_memories += f"{i}. {memory['content']}\n"
                if memory.get('metadata', {}).get('timestamp'):
                    try:
                        timestamp = datetime.datetime.fromisoformat(memory['metadata']['timestamp'])
                        formatted_time = timestamp.strftime("%Y-%m-%d")
                        formatted_memories += f"   (Recorded on: {formatted_time})\n"
                    except:
                        pass
                formatted_memories += "\n"
            
            return formatted_memories
        
        # Perform search
        memories = search_memory(query or "insurance policy claim denial appeal", limit=limit)
        
        # Create response
        response = {
            "memories": memories,
            "count": len(memories),
            "status": "success"
        }
        
        # Add formatted output if requested
        if formatted and query:
            response["formatted_output"] = get_relevant_memories(query, limit=limit)
        
        return response
    except Exception as e:
        import traceback
        error_detail = f"Error retrieving memories: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        return {
            "memories": [],
            "count": 0,
            "formatted_output": None,
            "status": f"error: {str(e)}"
        }

@app.get("/all-memories")
async def get_all_memories():
    """
    Get all memories in the database without requiring a search query.
    
    Returns:
    - List of all memories in the database
    """
    if not vectorstore:
        return {
            "memories": [],
            "count": 0,
            "status": "error: vector database not available"
        }
    
    try:
        # Get all point IDs from the collection
        point_count = vectorstore.client.count("insurance_research").count
        if point_count == 0:
            return {
                "memories": [],
                "count": 0,
                "status": "success"
            }
        
        # Get all points (limited to 100 for safety)
        limit = min(point_count, 100)
        
        # Get all points
        points = vectorstore.client.scroll(
            collection_name="insurance_research",
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        # Format the results
        memories = []
        for point in points[0]:
            point_id = point.id
            payload = point.payload
            
            # Extract content and metadata
            content = payload.get("page_content", "")
            metadata = {k: v for k, v in payload.items() if k != "page_content"}
            
            memories.append({
                "content": content,
                "metadata": metadata,
                "id": point_id
            })
        
        # Create response
        response = {
            "memories": memories,
            "count": len(memories),
            "status": "success"
        }
        
        return response
    except Exception as e:
        import traceback
        error_detail = f"Error retrieving all memories: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        return {
            "memories": [],
            "count": 0,
            "status": f"error: {str(e)}"
        }

# If running as a script, start an ASGI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
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
import sys
import shutil
import datetime
import uuid
import traceback
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file if present
load_dotenv()

# Configure path for imports - handle both local and Render deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Different path configurations to try
paths_to_try = [
    current_dir,                         # Current directory
    parent_dir,                          # Parent directory
    os.path.dirname(parent_dir),         # Grandparent directory 
    os.path.join(parent_dir, "my_agent") # my_agent in parent directory
]

# Add these paths to sys.path
for path in paths_to_try:
    if path not in sys.path:
        sys.path.append(path)
        print(f"Added to path: {path}")

# Import state management immediately to check path configuration
try:
    from my_agent.utils.state import AgentState
    print("Successfully imported AgentState - path configuration appears correct")
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Attempting direct import...")
    try:
        # Try relative import as a fallback
        sys.path.append('.')
        from utils.state import AgentState
        print("Successfully imported AgentState via direct import")
    except ImportError as e2:
        print(f"⚠️ Failed fallback import: {e2}")
        print("WARNING: Will attempt imports at runtime when endpoint is called")

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

class EmailInput(BaseModel):
    email: dict

class ResponseOutput(BaseModel):
    draft: str

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

@app.get("/health")
async def health():
    """
    Simple health check endpoint.
    """
    return {
        "status": "ok",
        "message": "API is running"
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
                    "source": "knowledge_base",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(days=60)).isoformat(),
                    "id": str(uuid.uuid4())
                }
            }
        ]
        
        # Add to vector store
        docs = []
        memory_ids = []
        for memory in memories:
            doc = Document(
                page_content=memory["content"],
                metadata=memory["metadata"]
            )
            docs.append(doc)
            memory_ids.append(memory["metadata"]["id"])
        
        # Add documents to vector store
        vectorstore.add_documents(docs)
        
        return {
            "success": True,
            "message": f"Added {len(docs)} test memories to database",
            "memory_ids": memory_ids
        }
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"Error creating test memories: {e}\n{error_detail}")
        return {
            "success": False,
            "message": f"Error creating memories: {str(e)}",
            "memory_ids": []
        }

@app.get("/memories", response_model=MemoryResponse)
async def get_memories(
    query: str = Query(None, description="Search query string"),
    limit: int = Query(10, description="Maximum number of results"),
    formatted: bool = Query(False, description="Return formatted memory context")
):
    """
    Get memories from the vector database.
    
    Parameters:
    - query: Search query string
    - limit: Maximum number of results to return
    - formatted: If true, return a formatted context string suitable for LLM prompts
    
    Returns:
    - List of matching memory objects with metadata and relevance scores
    - Formatted context string (if formatted=true)
    """
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
        error_detail = f"Error retrieving all memories: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        return {
            "memories": [],
            "count": 0,
            "status": f"error: {str(e)}"
        }

@app.post("/generate-response", response_model=ResponseOutput)
async def generate_response(email_input: EmailInput):
    """
    Generate a response to an insurance-related email using the complete Gmail Agent workflow.
    """
    try:
        # Log the incoming email data
        print(f"Received email for response generation:")
        print(f"  Subject: {email_input.email.get('subject', 'No Subject')}")
        print(f"  From: {email_input.email.get('sender', 'Unknown')}")
        print(f"  Email ID: {email_input.email.get('id', 'No ID')}")

        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Import the agent workflow nodes with error handling
        try:
            # First try the my_agent.utils style import (standard package import)
            from my_agent.utils.nodes import classify_email as classify_email_node
            from my_agent.utils.nodes import research as research_node
            from my_agent.utils.nodes import memory_injection as memory_injection_node
            from my_agent.utils.nodes import generate_response as generate_response_node
            from my_agent.utils.nodes import evaluate_response_quality as evaluate_response_node
            from my_agent.utils.nodes import flag_email as flag_email_node
            from my_agent.utils.state import AgentState
            from my_agent.utils.nodes import classification_router
            print("Successfully imported modules using my_agent.utils.* path")
        except ImportError as e:
            print(f"Primary import failed: {e}")
            try:
                # Try direct imports as fallback (for different directory structures)
                from utils.nodes import classify_email as classify_email_node
                from utils.nodes import research as research_node
                from utils.nodes import memory_injection as memory_injection_node
                from utils.nodes import generate_response as generate_response_node
                from utils.nodes import evaluate_response_quality as evaluate_response_node
                from utils.nodes import flag_email as flag_email_node
                from utils.state import AgentState
                from utils.nodes import classification_router
                print("Successfully imported modules using direct utils.* path")
            except ImportError as e2:
                print(f"Both import methods failed: {e2}")
                # Fallback to simple response generation if workflow modules can't be imported
                fallback_client = OpenAI(api_key=openai_api_key)
                prompt = f"""
                Generate a professional response to this insurance-related email:
                Subject: {email_input.email.get('subject', 'No Subject')}
                From: {email_input.email.get('sender', 'Unknown')}
                Body: {email_input.email.get('body', '')}
                """
                response = fallback_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant specializing in insurance matters."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                draft = response.choices[0].message.content.strip()
                print("⚠️ USING FALLBACK RESPONSE GENERATOR due to import failures")
                return {"draft": draft}
        
        # Create a Gmail-style message object to match what the nodes expect
        email_obj = {
            'id': email_input.email.get('id', 'api_email_id'),
            'threadId': email_input.email.get('threadId', 'api_thread_id'),
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': email_input.email.get('subject', 'No Subject')},
                    {'name': 'From', 'value': email_input.email.get('sender', 'sender@example.com')}
                ],
                'body': {'data': ''},
                'parts': [{'mimeType': 'text/plain', 'body': {'data': ''}}]
            }
        }
        
        # If the email has a body, add it to the parts
        if email_input.email.get('body'):
            # Convert the body to base64 to match Gmail API format
            import base64
            body_b64 = base64.b64encode(email_input.email.get('body', '').encode('utf-8')).decode('utf-8')
            email_obj['payload']['parts'][0]['body']['data'] = body_b64
        
        # Wrap everything in try/except blocks to handle potential errors in each component
        try:
            # Initialize agent state
            state = AgentState(
                new_email=email_obj,
                initialized=True,
                messages=[],
                email_classification=None
            )
            
            print("\n" + "="*80)
            print("STARTING FULL GMAIL AGENT WORKFLOW")
            print("="*80)
            
            # STEP 1: Classify the email as insurance-related or not
            print("\nSTEP 1: CLASSIFYING EMAIL")
            try:
                state = classify_email_node(state)
                classification = state.get('email_classification', 'Unknown')
                print(f"Email classification: {classification}")
                
                # Check if email is insurance related
                route = classification_router(state)
                print(f"Classification route: {route}")
                
                if route == 'flag_email':
                    print("Email is not insurance related. Skipping processing.")
                    return {"draft": "This email does not appear to be insurance-related. A standard response would be appropriate."}
            except Exception as classify_err:
                print(f"Error in classification step: {classify_err}")
                print("Continuing with workflow assuming email is insurance-related")
            
            # STEP 2: Perform research based on email content
            print("\nSTEP 2: PERFORMING RESEARCH")
            try:
                state = research_node(state)
                research_results = state.get('research_results', [])
                print(f"Research complete. Found {len(research_results)} results.")
            except Exception as research_err:
                print(f"Error in research step: {research_err}")
                print("Continuing workflow without research results")
                state['research_results'] = []
            
            # STEP 3: Inject relevant memories
            print("\nSTEP 3: INJECTING MEMORIES")
            try:
                state = memory_injection_node(state)
                memory_context = state.get('memory_context', '')
                if memory_context:
                    print(f"Memory context injected. Length: {len(memory_context)}")
                else:
                    print("No relevant memories found.")
            except Exception as memory_err:
                print(f"Error in memory injection step: {memory_err}")
                print("Continuing workflow without memory context")
                state['memory_context'] = ''
            
            # STEP 4: Generate initial response
            print("\nSTEP 4: GENERATING INITIAL RESPONSE")
            try:
                state = generate_response_node(state)
                initial_response = state.get('llm_output', '')
                print(f"Initial response generated. Length: {len(initial_response)}")
            except Exception as response_err:
                print(f"Error in response generation step: {response_err}")
                print("Falling back to simple response generation")
                
                # Fallback response generation
                client = OpenAI(api_key=openai_api_key)
                prompt = f"""
                Generate a professional response to this insurance-related email:
                Subject: {email_input.email.get('subject', 'No Subject')}
                From: {email_input.email.get('sender', 'Unknown')}
                Body: {email_input.email.get('body', '')}
                """
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant specializing in insurance matters."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                initial_response = response.choices[0].message.content.strip()
                state['llm_output'] = initial_response
            
            needs_more_research = False
            
            # STEP 5: Evaluate response quality
            print("\nSTEP 5: EVALUATING RESPONSE")
            try:
                state = evaluate_response_node(state)
                needs_more_research = state.get('needs_more_research', False)
            except Exception as eval_err:
                print(f"Error in evaluation step: {eval_err}")
                print("Skipping evaluation due to error")
            
            # STEP 6: Perform additional research cycles if needed
            final_response = initial_response
            if needs_more_research:
                print("\nSTEP 6: PERFORMING ADDITIONAL RESEARCH")
                try:
                    state = research_node(state)
                    state = memory_injection_node(state)
                    state = generate_response_node(state)
                    state = evaluate_response_node(state)
                    final_response = state.get('llm_output', initial_response)
                    print(f"Response after additional research. Length: {len(final_response)}")
                except Exception as additional_err:
                    print(f"Error in additional research cycle: {additional_err}")
                    print("Using initial response due to error in additional research")
                    final_response = initial_response
            else:
                print("No additional research needed.")
            
            # STEP 7: Flag the email (would mark as processed in actual flow)
            print("\nSTEP 7: FLAGGING EMAIL")
            try:
                state = flag_email_node(state)
            except Exception as flag_err:
                print(f"Error in flagging step: {flag_err}")
            
            print("\n" + "="*80)
            print("GMAIL AGENT WORKFLOW COMPLETE")
            print("="*80)
            
            # Return the final response
            return {"draft": final_response}
            
        except Exception as workflow_err:
            print(f"Workflow execution error: {workflow_err}")
            print(traceback.format_exc())
            
            # Final fallback for any workflow errors
            client = OpenAI(api_key=openai_api_key)
            prompt = f"""
            Generate a professional response to this insurance-related email:
            Subject: {email_input.email.get('subject', 'No Subject')}
            From: {email_input.email.get('sender', 'Unknown')}
            Body: {email_input.email.get('body', '')}
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant specializing in insurance matters."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            fallback_response = response.choices[0].message.content.strip()
            return {"draft": fallback_response}
    
    except Exception as e:
        print(f"Error generating response with full workflow: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# If running as a script, start an ASGI server
if __name__ == "__main__":
    import uvicorn
    print("Starting Gmail Agent API server on port 10000...")
    uvicorn.run(app, host="0.0.0.0", port=10000) 
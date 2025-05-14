#!/usr/bin/env python3
"""
API endpoint for Gmail Agent.
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
import os
import sys
import datetime
import uuid
import traceback
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
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

# Import state management
try:
    from my_agent.utils.state import AgentState
except ImportError:
    try:
        from utils.state import AgentState
    except ImportError:
        print("WARNING: Could not import AgentState. Will try again at runtime.")

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
api_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_db")

try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        
        # Connect to local Qdrant
        client = QdrantClient(path=api_db_path)
        
        # Check if collection exists and create if needed
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if not "insurance_research" in collection_names:
            client.recreate_collection(
                collection_name="insurance_research",
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        
        # Initialize vector store with the client
        vectorstore = Qdrant(
            client=client,
            collection_name="insurance_research",
            embeddings=embeddings,
        )
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
        "message": "Gmail Agent API is running",
        "vector_database_status": db_status,
        "available_endpoints": [
            {
                "path": "/memories",
                "description": "Get relevant memories",
                "example": "/memories?query=denial&limit=5&formatted=true"
            },
            {
                "path": "/status",
                "description": "Check the status of the system",
            },
            {
                "path": "/generate-response",
                "description": "Generate a response to an email",
                "method": "POST"
            }
        ]
    }

@app.get("/status")
async def status():
    """
    Return the status of the system and database connections.
    """
    return {
        "vector_database": {
            "available": vectorstore is not None,
            "type": f"Qdrant (local at {api_db_path})" if vectorstore else "Not connected"
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

@app.post("/generate-response", response_model=ResponseOutput)
async def generate_response(email_input: EmailInput):
    """
    Generate a response to an insurance-related email using the complete Gmail Agent workflow.
    """
    try:
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Import the agent workflow nodes
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
        except ImportError:
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
            except ImportError as e2:
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
        
        # Initialize agent state
        state = AgentState(
            new_email=email_obj,
            initialized=True,
            messages=[],
            email_classification=None
        )
        
        # STEP 1: Classify the email as insurance-related or not
        try:
            state = classify_email_node(state)
            
            # Check if email is insurance related
            route = classification_router(state)
            
            if route == 'flag_email':
                return {"draft": "This email does not appear to be insurance-related. A standard response would be appropriate."}
        except Exception:
            # Continue with workflow assuming email is insurance-related
            pass
        
        # STEP 2: Perform research based on email content
        try:
            state = research_node(state)
        except Exception:
            state['research_results'] = []
        
        # STEP 3: Inject relevant memories
        try:
            state = memory_injection_node(state)
        except Exception:
            state['memory_context'] = ''
        
        # STEP 4: Generate initial response
        try:
            state = generate_response_node(state)
            initial_response = state.get('llm_output', '')
        except Exception:
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
        
        # STEP 5: Evaluate response quality
        try:
            state = evaluate_response_node(state)
            needs_more_research = state.get('needs_more_research', False)
        except Exception:
            needs_more_research = False
        
        # STEP 6: Perform additional research cycles if needed
        final_response = initial_response
        if needs_more_research:
            try:
                state = research_node(state)
                state = memory_injection_node(state)
                state = generate_response_node(state)
                state = evaluate_response_node(state)
                final_response = state.get('llm_output', initial_response)
            except Exception:
                final_response = initial_response
        
        # STEP 7: Flag the email (would mark as processed in actual flow)
        try:
            state = flag_email_node(state)
        except Exception:
            pass
        
        # Return the final response
        return {"draft": final_response}
            
    except Exception as e:
        # Final fallback for any workflow errors
        try:
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
        except Exception:
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# If running as a script, start an ASGI server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port) 
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
import os
import sys
import datetime
import uuid
import traceback
import logging
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gmail_agent")

logger.info("Starting Gmail Agent API server")
load_dotenv()
logger.info("Environment variables loaded")

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)


paths_to_try = [
    current_dir,                         
    parent_dir,                          
    os.path.dirname(parent_dir),         
    os.path.join(parent_dir, "my_agent") 
]

for path in paths_to_try:
    if path not in sys.path:
        sys.path.append(path)

try:
    from my_agent.utils.state import AgentState
except ImportError:
    try:
        from utils.state import AgentState
    except ImportError:
        print("WARNING: Could not import AgentState. Will try again at runtime.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)


vectorstore = None
api_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_db")

try:
    logger.info(f"Initializing vector database at {api_db_path}")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        logger.info("OpenAI API key found, initializing embeddings")
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        client = QdrantClient(path=api_db_path)
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        logger.info(f"Found collections: {collection_names}")
        
        if not "insurance_research" in collection_names:
            logger.info("Creating 'insurance_research' collection")
            client.recreate_collection(
                collection_name="insurance_research",
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        vectorstore = Qdrant(
            client=client,
            collection_name="insurance_research",
            embeddings=embeddings,
        )
        logger.info("Vector database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize vector database: {e}")
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


@app.get("/status")
async def status():
    """
    Return the status of the system and database connections.
    """
    logger.info("Status endpoint called")
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
    logger.info("Health check endpoint called")
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
    logger.info(f"Memories endpoint called with query='{query}', limit={limit}, formatted={formatted}")
    try:
        def search_memory(query: str, limit: int = 3) -> List[Dict]:
            if not vectorstore:
                logger.warning("Vector store not available for memory search")
                return []
            
            try:
                logger.info(f"Searching for '{query}' with limit {limit}")
                results = vectorstore.similarity_search_with_score(query, k=limit)
                logger.info(f"Found {len(results)} results")
                
                memory_results = []
                for doc, score in results:
                    memory_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance_score": float(score)
                    })
                
                return memory_results
            except Exception as e:
                logger.error(f"Error searching memory: {e}")
                print(f"Error searching memory: {e}")
                return []
                
        def get_relevant_memories(query: str, limit: int = 5) -> str:
            logger.info(f"Formatting relevant memories for '{query}'")
            memories = search_memory(query, limit=limit)
            
            if not memories:
                return ""
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
        
        memories = search_memory(query or "insurance policy claim denial appeal", limit=limit)
        logger.info(f"Returning {len(memories)} memories")
        response = {
            "memories": memories,
            "count": len(memories),
            "status": "success"
        }
        if formatted and query:
            logger.info("Adding formatted output to response")
            response["formatted_output"] = get_relevant_memories(query, limit=limit)
        
        return response
    except Exception as e:
        error_detail = f"Error retrieving memories: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
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
    logger.info("Generate response endpoint called")
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OpenAI API key not configured")
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        logger.info("Importing processing nodes")
        try:
            from my_agent.utils.nodes import classify_email as classify_email_node
            from my_agent.utils.nodes import research as research_node
            from my_agent.utils.nodes import memory_injection as memory_injection_node
            from my_agent.utils.nodes import generate_response as generate_response_node
            from my_agent.utils.nodes import evaluate_response_quality as evaluate_response_node
            from my_agent.utils.nodes import flag_email as flag_email_node
            from my_agent.utils.state import AgentState
            from my_agent.utils.nodes import classification_router
            logger.info("Successfully imported nodes from my_agent.utils")
        except ImportError:
            logger.warning("Import from my_agent.utils failed, trying direct imports")
            try:
                from utils.nodes import classify_email as classify_email_node
                from utils.nodes import research as research_node
                from utils.nodes import memory_injection as memory_injection_node
                from utils.nodes import generate_response as generate_response_node
                from utils.nodes import evaluate_response_quality as evaluate_response_node
                from utils.nodes import flag_email as flag_email_node
                from utils.state import AgentState
                from utils.nodes import classification_router
                logger.info("Successfully imported nodes from utils")
            except ImportError as e2:
                logger.error(f"Failed to import processing nodes: {e2}")
                logger.info("Using fallback OpenAI direct response")
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
        
        logger.info("Preparing email object")
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
        
        if email_input.email.get('body'):
            import base64
            body_b64 = base64.b64encode(email_input.email.get('body', '').encode('utf-8')).decode('utf-8')
            email_obj['payload']['parts'][0]['body']['data'] = body_b64
        
        logger.info("Initializing agent state")
        state = AgentState(
            new_email=email_obj,
            initialized=True,
            messages=[],
            email_classification=None
        )
        
        try:
            logger.info("Running email classification")
            state = classify_email_node(state)
            route = classification_router(state)
            logger.info(f"Email classified as: {state.get('email_classification', 'unknown')}, route: {route}")
            
            if route == 'flag_email':
                logger.info("Email flagged as non-insurance related")
                return {"draft": "This email does not appear to be insurance-related. A standard response would be appropriate."}
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            pass
        
        try:
            logger.info("Running research node")
            state = research_node(state)
            logger.info(f"Research complete, found {len(state.get('research_results', []))} results")
        except Exception as e:
            logger.error(f"Research failed: {e}")
            state['research_results'] = []
        
        try:
            logger.info("Running memory injection")
            state = memory_injection_node(state)
            memory_length = len(state.get('memory_context', ''))
            logger.info(f"Memory injection complete, context length: {memory_length}")
        except Exception as e:
            logger.error(f"Memory injection failed: {e}")
            state['memory_context'] = ''
        
        try:
            logger.info("Generating initial response")
            state = generate_response_node(state)
            initial_response = state.get('llm_output', '')
            logger.info("Initial response generated")
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            logger.info("Using fallback response generation")
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
        
        try:
            logger.info("Evaluating response quality")
            state = evaluate_response_node(state)
            needs_more_research = state.get('needs_more_research', False)
            logger.info(f"Evaluation complete, needs more research: {needs_more_research}")
        except Exception as e:
            logger.error(f"Response evaluation failed: {e}")
            needs_more_research = False
        
        final_response = initial_response
        if needs_more_research:
            logger.info("Additional research needed, running second research phase")
            try:
                state = research_node(state)
                logger.info("Second research phase complete")
                state = memory_injection_node(state)
                logger.info("Second memory injection complete")
                state = generate_response_node(state)
                logger.info("Second response generation complete")
                state = evaluate_response_node(state)
                logger.info("Second evaluation complete")
                final_response = state.get('llm_output', initial_response)
            except Exception as e:
                logger.error(f"Second research phase failed: {e}")
                final_response = initial_response
        
        try:
            logger.info("Running final email flagging check")
            state = flag_email_node(state)
            logger.info(f"Email flagging complete: {state.get('flagged', False)}")
        except Exception as e:
            logger.error(f"Email flagging failed: {e}")
            pass
        
        logger.info("Returning final response")
        return {"draft": final_response}
            
    except Exception as e:
        logger.error(f"Overall process failed with error: {e}")
        try:
            logger.info("Using final fallback response")
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
        except Exception as fallback_error:
            logger.error(f"Final fallback also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 
import os
import base64
import quopri
import re
import uuid
import datetime
import json
from typing import List, Dict
from dotenv import load_dotenv
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.utils import build_resource_service, get_gmail_credentials
from langchain_core.tools import tool, BaseTool
from langchain_core.documents import Document
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from openai import OpenAI
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")
else:
    print(f"Using OpenAI API key")

openai_client = None
embeddings = None
vectorstore = None

if openai_api_key:
    openai_client = OpenAI(api_key=openai_api_key)
    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
    
    try:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if qdrant_url:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            print(f"Connected to Qdrant cloud at {qdrant_url}")
        else:
            client = QdrantClient(path="./qdrant_db")
            print("Connected to local Qdrant database")
        
        vectorstore = Qdrant(
            client=client,
            collection_name="insurance_research",
            embeddings=embeddings,
        )
        print("Qdrant vector store initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize Qdrant vector store: {e}")
else:
    print("Warning: Cannot initialize OpenAI client and vector store without an API key")

def send_email(service, to, subject, message_text, user_id="me", thread_id=None, message_id=None):
    email_match = re.search(r'<?([\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,})>?', to)
    
    if email_match:
        to_email = email_match.group(1)
    else:
        raise ValueError(f"Invalid email address format: {to}")
    
    print(f"Sending email to: {to_email}")
    
    message = MIMEMultipart()
    message["to"] = to_email
    message["subject"] = subject
    
    if message_id:
        message["In-Reply-To"] = message_id
        message["References"] = message_id
    
    message.attach(MIMEText(message_text, "plain"))
    
    raw = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')
    message_body = {"raw": raw}
    
    if thread_id:
        print(f"Using thread ID: {thread_id} for email threading")
        message_body["threadId"] = thread_id
    
    try:
        sent_message = service.users().messages().send(userId=user_id, body=message_body).execute()
        print(f"Email sent: ID {sent_message['id']}" + (f" in thread: {thread_id}" if thread_id else ""))
        return sent_message
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        if thread_id or message_id:
            print("Retrying without threading information...")
            return send_email(service, to, subject, message_text, user_id)
        else:
            raise


def get_email_body(payload):
    def decode_part(part):
        body = part.get("body", {}).get("data")
        if body:
            try:
                data = base64.urlsafe_b64decode(body.encode("UTF-8"))
                if part.get("mimeType") == "text/plain":
                    return data.decode("UTF-8", errors="replace")
                elif part.get("mimeType") == "text/html":
                    return quopri.decodestring(data).decode("UTF-8", errors="replace")
                else:
                    return f"[{part.get('mimeType', 'attachment')}]"
            except Exception as e:
                print(f"Error decoding email part: {e}")
                return f"[Unreadable content: {part.get('mimeType', 'unknown')}]"
        elif "parts" in part:
            return "".join(filter(None, [decode_part(p) for p in part["parts"]]))
        return ""
    return decode_part(payload)


def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label = next((label for label in labels if label['name'] == label_name), None)
    if label:
        return label['id']
    else:
        label_body = {
            'name': label_name,
            'labellistVisibility': 'labelShow',
            'messagelistVisibility': 'show',
            'type': 'user'
        }
        label = service.users().labels().create(userId='me', body=label_body).execute()
        return label['id']

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = """Search the internet for up-to-date information. Use this tool when:
1. You need to find current facts, news, or information not in your knowledge base
2. You need current date, time, weather, or other time-sensitive information
3. You need to clarify ambiguous terms, acronyms, or technical jargon in emails
4. You need to verify claims or statements made in emails
5. You need context about organizations, people, or products mentioned in emails
6. You need to research industry trends or background information relevant to email content
7. You need to research insurance policies, medical procedures, or billing codes"""
    
    def _run(self, query: str) -> str:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error performing web search: OPENAI_API_KEY not found in environment variables."
        
        local_client = OpenAI(api_key=api_key)
        print(f"[WebSearchTool] Created local OpenAI client with API key: {api_key[:4]}...{api_key[-4:]}")
        
        try:
            print(f"[WebSearchTool] Performing search for: '{query}'")
            
            try:
                if "insurance" in query.lower() or "policy" in query.lower() or "claim" in query.lower() or "appeal" in query.lower():
                    print("[WebSearchTool] Using specialized insurance research approach")
                    completion = local_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": """You are a specialized insurance researcher with access to the latest insurance regulations and practices. 
                            
For each query, provide a detailed, up-to-date answer that includes:
1. Current regulations and laws that apply (federal and state level)
2. Recent changes (2024-2025) that affect the topic
3. Practical steps and procedures for insurance matters
4. Citations to specific regulations or resources when possible

IMPORTANT: If information might be outdated (pre-2025), explicitly note this and recommend official verification.

Format your response with clear headings and bullet points for easy reading."""},
                            {"role": "user", "content": query}
                        ],
                        temperature=0.2
                    )
                    search_result = completion.choices[0].message.content
                    
                    search_result += "\n\n[NOTE: For the most current and authoritative information, please verify with your state's insurance department or the relevant federal agency as regulations may have changed recently.]"
                else:
                    print("[WebSearchTool] Using general search approach")
                    has_responses_api = hasattr(local_client, 'responses') and callable(getattr(local_client, 'responses', {}).get('create', None))
                    
                    if has_responses_api:
                        print("[WebSearchTool] Using OpenAI responses API with web search")
                        try:
                            response = local_client.responses.create(
                                model="gpt-4o",
                                tools=[{"type": "web_search_preview"}],
                                input=query
                            )
                            print("[WebSearchTool] Successfully called responses.create API")
                            
                            search_result = ""
                            if hasattr(response, 'output') and response.output:
                                for output_item in response.output:
                                    if hasattr(output_item, 'content') and output_item.content:
                                        for content_item in output_item.content:
                                            if hasattr(content_item, 'text'):
                                                search_result = content_item.text
                                                break
                        
                            if not search_result and hasattr(response, 'text'):
                                search_result = response.text
                            if not search_result:
                                search_result = str(response)
                        except Exception as e:
                            print(f"[WebSearchTool] Error with responses API: {e}. Falling back to standard completions.")
                            raise RuntimeError("Failed to use responses API") from e
                    else:
                        print("[WebSearchTool] OpenAI responses API not available, using chat completions")
                        raise AttributeError("responses API not available")
            except Exception as api_error:
                print(f"[WebSearchTool] Falling back to standard completions due to: {str(api_error)}")
                completion = local_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": """You are a helpful web search assistant. When responding:
1. Provide comprehensive, factual information based on your knowledge
2. Clearly indicate when information might be outdated (your training only includes data until 2023)
3. For recent events, explicitly note your knowledge cutoff date
4. Format responses with clear headings and bullet points
5. Include relevant dates, sources, or context where appropriate

When answering questions about current events, policies, or time-sensitive information, recommend verifying with up-to-date sources."""},
                        {"role": "user", "content": f"Search query: {query}\n\nPlease provide comprehensive information about this topic, including recent developments you're aware of. Note your knowledge limitations where appropriate."}
                    ],
                    temperature=0.2
                )
                search_result = completion.choices[0].message.content
            
            print("[WebSearchTool] Successfully received search results")
            
            preview_lines = search_result.strip().split('\n')[:5]
            preview = '\n'.join(preview_lines)
            if len(preview_lines) < len(search_result.strip().split('\n')):
                preview += "\n..."
            print(f"[WebSearchTool] Result preview:\n{preview}")
            
            try:
                if vectorstore:
                    doc_id = str(uuid.uuid4())
                    document = Document(
                        page_content=f"Web search for '{query}': {search_result}",
                        metadata={
                            "source": "web_search", 
                            "query": query, 
                            "id": doc_id, 
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    )
                    vectorstore.add_documents([document])
                    print(f"[WebSearchTool] Saved search result to Qdrant memory with ID: {doc_id}")
            except Exception as e:
                print(f"[WebSearchTool] Warning: Could not save search result to vector store: {e}")

            print(f"[WebSearchTool] Completed search for: '{query}' - Results length: {len(search_result)} characters")
            
            return search_result
        except Exception as e:
            error_msg = f"Error performing web search: {str(e)}"
            print(f"[WebSearchTool] ERROR: {error_msg}")
            return error_msg
    
    def _arun(self, query: str) -> str:
        raise NotImplementedError("This tool does not support async")


def search_memory(query: str, limit: int = 3) -> List[Dict]:
    if not vectorstore:
        return []
    
    try:
        results = vectorstore.similarity_search_with_score(query, k=limit)
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

def extract_and_store_memory(email_content: str, search_results: List[Dict], response: str) -> str:
    if not vectorstore or not openai_client:
        print("Cannot extract memory: vector store or OpenAI client not initialized")
        return None
    
    try:
        extraction_prompt = f"""
        Extract the most important facts from this insurance-related email exchange.
        Focus on:
        1. Insurance policy details (policy numbers, coverage limits, terms)
        2. Medical conditions, treatments, and codes mentioned
        3. Claim details and reasons for denial
        4. Laws, regulations, or precedents referenced
        5. Key dates and deadlines
        6. Action items or next steps
        
        EMAIL CONTENT:
        {email_content}
        
        RESEARCH INFORMATION:
        {json.dumps([r.get('result', '') for r in search_results], indent=2)}
        
        AGENT RESPONSE:
        {response}
        
        Summarize the most important information in a concise format:
        """
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts and summarizes key insurance information from emails."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.2,
        )
        
        memory_content = completion.choices[0].message.content
        doc_id = str(uuid.uuid4())
        document = Document(
            page_content=memory_content,
            metadata={
                "source": "email_exchange", 
                "timestamp": datetime.datetime.now().isoformat(),
                "id": doc_id
            }
        )
        
        try:
            collections = vectorstore.client.get_collections()
            if not any(c.name == "insurance_research" for c in collections.collections):
                print("Creating 'insurance_research' collection")
                vectorstore.client.recreate_collection(
                    collection_name="insurance_research",
                    vectors_config={"size": 1536, "distance": "Cosine"}
                )
        except Exception as collection_err:
            print(f"Error checking/creating collection: {collection_err}")
        vectorstore.add_documents([document])
        
        print(f"Stored memory with ID: {doc_id}")
        print(f"Memory content: {memory_content[:200]}...")
        
        return doc_id
        
    except Exception as e:
        print(f"Error extracting and storing memory: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def get_relevant_memories(query: str, limit: int = 5) -> str:
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
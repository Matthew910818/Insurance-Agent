from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import GmailToolkit 
from my_agent.utils.state import AgentState
from my_agent.utils.tools import send_email, get_email_body, get_or_create_label, WebSearchTool, search_memory

import os
import base64
import quopri
import json
import re
import tempfile
from typing_extensions import TypedDict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from openai import OpenAI
import time


def get_gmail_service():
    print("=== CREDENTIAL DEBUG INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    
    client_secrets_json = os.getenv("GMAIL_CLIENT_SECRETS_JSON")
    token_json = os.getenv("GMAIL_TOKEN_JSON")
    
    client_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False)
    client_file.write(client_secrets_json)
    client_file.close()
    client_secrets_path = client_file.name
    
    token_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False)
    token_file.write(token_json)
    token_file.close()
    token_path = token_file.name
    
    print(f"Created temporary files: {client_secrets_path}, {token_path}")
    
    try:
        creds = Credentials.from_authorized_user_file(token_path, ["https://mail.google.com/"])
        
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Gmail service: {str(e)}") from e
    finally:
        try:
            os.unlink(client_secrets_path)
            os.unlink(token_path)
        except:
            pass

try:
    print("Initializing Gmail service...")
    service = get_gmail_service()
    print("Gmail service initialized successfully")
except Exception as e:
    print(f"Error initializing Gmail service: {str(e)}")
    print("Without Gmail service, email functions will not work properly.")
    print("Please ensure you have:")
    print("1. A valid credentials.json file from Google Cloud Console")
    print("2. Run the authenticate.py script to generate token.json")
    service = None

def get_llm(temperature=0, model_name="gpt-4o-mini"):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(
        temperature=temperature, 
        model_name=model_name,
        openai_api_key=openai_api_key
    )

def agent(state: AgentState):
    if "messages" not in state:
        state["messages"] = []
    
    if "initialized" not in state:
        state["initialized"] = False
    
    print("Agent node initialized the workflow")
    return state

def check_for_new_emails(state: AgentState):  
    if not state.get('initialized', False):
        state['initialized'] = True
        state['polling_cycle'] = 0 
        try:
            results = service.users().messages().list(
                userId='me', 
                labelIds=['INBOX', 'UNREAD'],
                maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            if messages:
                state['processed_email_ids'] = [msg['id'] for msg in messages]
                print(f"Initial emails marked as processed: {len(state['processed_email_ids'])} emails")
            else:
                state['processed_email_ids'] = []
                print("No initial emails found to mark as processed")
                
            state['new_email'] = None
            state['continue_polling'] = True
        except Exception as e:
            print(f"Error initializing email processing: {e}")
            state['error'] = f"Error accessing Gmail: {str(e)}"
            state['new_email'] = None
            state['continue_polling'] = False
        return state
    
    state['polling_cycle'] = state.get('polling_cycle', 0) + 1
    print(f"\n{'='*80}")
    print(f"EMAIL POLLING CYCLE #{state['polling_cycle']}")
    print(f"{'='*80}")
    
    try:
        inbox_results = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX'],
            maxResults=1
        ).execute()
        
        unread_results = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX', 'UNREAD'],
            maxResults=1
        ).execute()
        
        labels = service.users().labels().list(userId='me').execute().get('labels', [])
        inbox_label = next((label for label in labels if label['name'] == 'INBOX'), None)
        unread_label = next((label for label in labels if label['name'] == 'UNREAD'), None)
        
        total_inbox = inbox_label.get('messagesTotal', 0) if inbox_label else 0
        total_unread = unread_label.get('messagesTotal', 0) if unread_label else 0
        
        print(f"MAILBOX STATUS: {total_unread} unread messages out of {total_inbox} total in inbox")
    except Exception as e:
        print(f"Could not retrieve mailbox status: {e}")
    
    if state.get('polling_cycle', 0) > 1: 
        delay_seconds = 5 
        print(f"Waiting {delay_seconds} seconds before checking emails...")
        time.sleep(delay_seconds)
    
    try:
        results = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX', 'UNREAD'],
            maxResults=5
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            print("No unread messages found in inbox")
            state['new_email'] = None
            
            if state.get('polling_cycle', 0) >= 5: 
                print("Maximum polling cycles reached. Stopping email check.")
                state['continue_polling'] = False
            else:
                print(f"No unread emails found. Will check again in next polling cycle.")
                state['continue_polling'] = True
                
            return state
            
        processed_ids = set(state.get('processed_email_ids', []))
        print(f"Found {len(messages)} unread messages, {len(processed_ids)} already in processed list")
        emails_to_process = [msg for msg in messages if msg['id'] not in processed_ids]
        
        if emails_to_process:
            email_id = emails_to_process[-1]['id']
            print(f"Found new unread email with ID: {email_id}")

            email = service.users().messages().get(
                userId='me', 
                id=email_id, 
                format='full'
            ).execute()
            
            state['new_email'] = email
            state['continue_polling'] = False
            print("New email loaded into state")
            if email_id not in processed_ids:
                if 'processed_email_ids' not in state:
                    state['processed_email_ids'] = []
                state['processed_email_ids'].append(email_id)
                print(f"Pre-emptively added email ID {email_id} to processed list")
                
        else:
            print("No new unread emails to process")
            state['new_email'] = None
            
            if state.get('polling_cycle', 0) >= 5: 
                print("Maximum polling cycles reached. Stopping email check.")
                state['continue_polling'] = False
            else:
                print(f"No new unread emails found. Will check again in next polling cycle.")
                state['continue_polling'] = True
            
    except Exception as e:
        print(f"Error checking for new emails: {e}")
        state['error'] = f"Error accessing Gmail: {str(e)}"
        state['new_email'] = None
        state['continue_polling'] = False
        
    return state

class GradeEmail(BaseModel):
    score: str = Field(description="Is the email medical insurance related? If yes -> 'Yes', if not -> 'No'")

def classify_email(state: AgentState):
    email = state.get('new_email')
    if not email:
        state['email_classification'] = 'No new email'
        return state
    payload = email.get('payload', {})
    headers = payload.get('headers', [])
    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
    sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
    body = get_email_body(payload)
    email_content = f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    try:
        llm = get_llm()
        try:
            system_prompt = """You are an assistant that classifies emails. If the email is medical debt insurance related, classify it as 'Yes', otherwise as 'No'.
Yes - e.g., Insurance Denail Claim."""
            grade_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", "Email content:\n\n{email_content}\n\nIs this an debt insurance related email? 'Yes' or 'No'?"),
                ]
            )
            
            try:
                structured_llm = llm.with_structured_output(GradeEmail)
                classifier = grade_prompt | structured_llm
                result = classifier.invoke({"email_content": email_content})
                state['email_classification'] = result.score
            except AttributeError:
                from langchain.pydantic_v1 import BaseModel, Field
                from langchain.chains.structured_output import create_structured_output_chain
                
                class GradeEmailV1(BaseModel):
                    score: str = Field(description="Is the email medical debt insurance related? If yes -> 'Yes', if not -> 'No'")
                
                chain = create_structured_output_chain(GradeEmailV1, llm, grade_prompt)
                result = chain.invoke({"email_content": email_content})
                state['email_classification'] = result["score"]
                
        except Exception as e:
            print(f"Error using LangChain structured output: {e}")
            openai_api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an assistant that classifies emails. If the email is medical debt insurance related, answer 'Yes', otherwise answer 'No'."},
                    {"role": "user", "content": f"Email content:\n\n{email_content}\n\nIs this an debt insurance related email? Answer only with 'Yes' or 'No'."}
                ],
                temperature=0
            )
            state['email_classification'] = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Final fallback classification error: {e}")
        if any(term in email_content.lower() for term in ['insurance', 'policy', 'claim', 'coverage', 'premium']):
            state['email_classification'] = 'Yes'
        else:
            state['email_classification'] = 'No'
    
    print("Updated state in 'classify_email':", state)
    return state

def new_email_router(state: AgentState):
    if not state.get('initialized', False):
        return "__end__"
    elif state.get('new_email'):
        return 'classify_email'
    else:
        return "__end__"
    
def classification_router(state: AgentState):
    classification = state.get('email_classification', '').lower()
    if classification == 'yes':
        return 'research'
    elif classification == 'no':
        return 'flag_email'
    else:
        raise ValueError(f"Unexpected classification value: {classification}")
    
def research(state: AgentState):
    email = state.get('new_email')
    if not email:
        print("No email to research.")
        return state
    
    try:
        print("\n" + "="*80)
        print("STARTING RESEARCH PROCESS")
        print("="*80)
        
        if state.get('research_cycles', 0) > 0:
            print(f"RESEARCH CYCLE #{state['research_cycles']}")
        
        web_search_tool = WebSearchTool()
        print("[Research] WebSearchTool initialized in research function")
        
        payload = email.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
        sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
        body = get_email_body(payload)
        email_content = f"From: {sender}\nSubject: {subject}\n\n{body}"
        
        print(f"[Research] Email subject: {subject}")
        print(f"[Research] Email sender: {sender}")
        print(f"[Research] Email body length: {len(body)} characters")
        
        if state.get('research_cycles', 0) > 0 and 'additional_queries' in state:
            search_queries = state['additional_queries']
            print(f"[Research] Using additional queries from previous cycle: {search_queries}")
        else:
            llm = get_llm()
            query_prompt = ChatPromptTemplate.from_messages([
                ("system", """Generate up to 3 focused search queries to help research this insurance-related email. 
Format your response as a JSON list of query strings. 
Example: ["query 1", "query 2", "query 3"]"""),
                ("human", "Insurance email content:\n\n{email_content}")
            ])
            
            chain = query_prompt | llm | StrOutputParser()
            search_queries_json = chain.invoke({"email_content": email_content})
            print(f"[Research] Generated search queries JSON: {search_queries_json}")

            search_queries_json = re.sub(r'^```json', '', search_queries_json)
            search_queries_json = re.sub(r'```$', '', search_queries_json)
            search_queries_json = search_queries_json.strip()
            
            try:
                search_queries = json.loads(search_queries_json)
                if isinstance(search_queries, list):
                    search_queries = search_queries[:3]
                else:
                    search_queries = [search_queries_json]
            except json.JSONDecodeError as je:
                print(f"[Research] Failed to parse search queries JSON: {search_queries_json}")
                print(f"[Research] JSON error: {je}")
                search_queries = [f"insurance policy terms for {subject}"]
        
        print(f"[Research] Final search queries: {search_queries}")
        
        memory_results = []
        for query in search_queries:
            print(f"[Research] Checking memory for: {query}")
            try:
                memory_hits = search_memory(query, limit=2)
                if memory_hits:
                    memory_results.append({
                        "query": query,
                        "source": "memory",
                        "results": memory_hits
                    })
                    print(f"[Research] Found {len(memory_hits)} relevant memory results for: {query}")
                else:
                    print(f"[Research] No memory results for: {query}")
            except Exception as memory_err:
                print(f"[Research] Error searching memory for '{query}': {memory_err}")
        
        web_search_results = []
        for i, query in enumerate(search_queries):
            memory_match = any(r["query"] == query for r in memory_results)
            
            if not memory_match or len(memory_results) == 0:
                print(f"\n{'*'*40}")
                print(f"[Research] WEB SEARCH #{i+1}: {query}")
                print(f"{'*'*40}")
                
                try:
                    print("[Research] Calling WebSearchTool._run()")
                    result = web_search_tool._run(query)
                    
                    if result.startswith("Error performing web search"):
                        print(f"[Research] Web search error: {result}")
                        result = f"Error performing web search: {result}"
                    
                    print("\n" + "-"*80)
                    print(f"[Research] SEARCH RESULT FOR: {query}")
                    print("-"*80)
                    
                    preview_lines = result.strip().split('\n')[:10] 
                    preview = '\n'.join(preview_lines)
                    if len(preview_lines) < len(result.strip().split('\n')):
                        preview += "\n..."
                    print(f"{preview}")
                    print("-"*80 + "\n")
                    
                    web_search_results.append({
                        "query": query,
                        "source": "web_search",
                        "result": result
                    })
                except Exception as web_err:
                    print(f"[Research] Exception in web search for '{query}': {web_err}")
                    web_search_results.append({
                        "query": query,
                        "source": "web_search_failed",
                        "result": "Could not perform web search due to a technical error. Please review policy documentation directly."
                    })
            else:
                print(f"[Research] Skipping web search for '{query}' - found in memory")
        
        if state.get('research_cycles', 0) > 0 and 'research_results' in state:
            existing_results = state['research_results']
            print(f"[Research] Combining with {len(existing_results)} existing research results")
        else:
            existing_results = []
        
        combined_results = existing_results.copy() 
        
        for mem_item in memory_results:
            if not any(item['query'] == mem_item['query'] for item in combined_results):
                formatted_results = ""
                for hit in mem_item["results"]:
                    formatted_results += f"- {hit['content']}\n"
                
                combined_results.append({
                    "query": mem_item["query"],
                    "result": f"[FROM MEMORY] {formatted_results}"
                })
                print(f"[Research] Added memory result for: {mem_item['query']}")
        
        for web_item in web_search_results:
            if not any(item['query'] == web_item['query'] for item in combined_results):
                combined_results.append({
                    "query": web_item["query"],
                    "result": web_item["result"]
                })
                print(f"[Research] Added web search result for: {web_item['query']}")
        
        state['research_results'] = combined_results
        print(f"[Research] Research completed: {len(combined_results)} total results ({len(memory_results)} from memory, {len(web_search_results)} from web)")
        print("="*80)
        print("RESEARCH PROCESS COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        import traceback
        print(f"[Research] Error during research: {e}")
        print(traceback.format_exc())
        state['error'] = f"Error performing research: {str(e)}"
        state['research_results'] = [{
            "query": "insurance policy basics",
            "result": "When dealing with insurance claims, always verify coverage details in your policy, document all communications, and request written explanations for any denials. For appeals, gather supporting medical documentation and cite specific policy provisions."
        }]
    
    return state

def memory_injection(state: AgentState):
    email = state.get('new_email')
    if not email:
        print("No email to find memories for.")
        return state
    
    try:
        payload = email.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
        sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
        body = get_email_body(payload)
        email_content = f"From: {sender}\nSubject: {subject}\n\n{body}"
        print("\n" + "="*80)
        print("RETRIEVING RELEVANT MEMORIES")
        print("="*80)
        
        search_context = f"{subject} {body[:500]}"
        print(f"[Memory] Searching memories using context from email")
        
        from my_agent.utils.tools import get_relevant_memories
        memory_context = get_relevant_memories(search_context)
        
        if memory_context:
            print(f"[Memory] Found relevant memories: \n{'-'*50}\n{memory_context}\n{'-'*50}")
            state['memory_context'] = memory_context
            if 'debug' not in state:
                state['debug'] = {}
            state['debug']['memory_found'] = True
            state['debug']['memory_content'] = memory_context
        else:
            print("[Memory] No relevant memories found")
            state['memory_context'] = ""
            if 'debug' not in state:
                state['debug'] = {}
            state['debug']['memory_found'] = False
            
        print("="*80)
        print("MEMORY RETRIEVAL COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        import traceback
        print(f"[Memory] Error retrieving memories: {e}")
        print(traceback.format_exc())
        state['memory_context'] = ""
        if 'debug' not in state:
            state['debug'] = {}
        state['debug']['memory_error'] = str(e)
    
    return state

def generate_response(state: AgentState):
    email = state.get('new_email')
    payload = email.get('payload', {})
    headers = payload.get('headers', [])
    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
    sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
    body = get_email_body(payload)
    email_content = f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    research_context = ""
    if research_results := state.get('research_results', []):
        research_context = "\n\nResearch information:\n"
        for idx, item in enumerate(research_results, 1):
            research_context += f"\n{idx}. Query: {item['query']}\nResults: {item['result']}\n"
    
    memory_context = state.get('memory_context', '')
    if memory_context:
        research_context += f"\n\n{memory_context}"
    
    if 'research_cycles' not in state:
        state['research_cycles'] = 0
    
    cycle_info = ""
    if state.get('research_cycles', 0) > 0:
        cycle_info = f"\n\nThis is research cycle #{state['research_cycles']}. If you need more information to provide a complete response, indicate this in your analysis."
    
    system_prompt = """You are a professional healthcare insurance advocate who specializes in responding to insurance claim denials and rejections. 
Your responses should be formal, authoritative, and strategic, focusing on:

1. Clearly citing specific policy provisions, medical codes, and legal requirements that support your position
2. Assertively but professionally challenging any erroneous interpretations of coverage terms
3. Providing well-structured, factual arguments supported by evidence from the policy documentation
4. Using persuasive, professional language that emphasizes the medical necessity of treatments
5. Referencing relevant precedents or regulations when applicable (such as state insurance laws)
6. Including explicit follow-up steps and appeal procedures with specific timeframes
7. Maintaining a firm but diplomatic tone throughout the correspondence

IMPORTANT FORMATTING GUIDELINES:
- Do NOT include the word 'Subject:' in your response - this will be added automatically by the email system
- Do NOT use asterisks (*) for emphasis or formatting - use plain text only
- Use numbered and bulleted lists without special formatting characters
- Format sections with clear headings using ALL CAPS instead of any special formatting
- For emphasis, use CAPITALIZATION or underscores like_this instead of asterisks

For non-insurance emails, maintain a professional and courteous tone.

Only provide the complete email text. Do not include any explanations, headers, or formatting instructions outside the email itself."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Email content:\n\n{email_content}{research_info}{cycle_info}\n\nWrite a professional response that addresses the insurance claim issues with appropriate negotiation strategies if applicable.")
    ])
    
    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "email_content": email_content,
        "research_info": research_context,
        "cycle_info": cycle_info
    })
    response = response.replace('*', '')
    if response.lstrip().startswith("Subject:"):
        response = "\n".join(response.split("\n")[1:])
    lines = response.split("\n")
    if lines and lines[0].startswith("Re:"):
        lines[0] = lines[0][3:].lstrip()
        response = "\n".join(lines)
    
    state['llm_output'] = response
    state['needs_evaluation'] = True
    state['needs_more_research'] = False
    
    print("Updated state in 'generate_response':", state)
    return state

def evaluate_response_quality(state: AgentState):
    if state.get('research_cycles', 0) >= 2:  
        print("\n" + "="*80)
        print("RESPONSE EVALUATION: MAX CYCLES REACHED")
        print("="*80)
        print("Maximum research cycles reached. Proceeding with current response.")
        state['needs_more_research'] = False
        state['needs_evaluation'] = False 
        return state
    
    email = state.get('new_email')
    if not email:
        print("No email to evaluate.")
        state['needs_more_research'] = False
        state['needs_evaluation'] = False
        return state
    
    response = state.get('llm_output', '')
    if not response:
        print("No response to evaluate.")
        state['needs_more_research'] = False
        state['needs_evaluation'] = False
        return state
    
    payload = email.get('payload', {})
    headers = payload.get('headers', [])
    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
    sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
    body = get_email_body(payload)
    email_content = f"From: {sender}\nSubject: {subject}\n\n{body[:500]}..." 
    
    print("\n" + "="*80)
    print("EVALUATING RESPONSE QUALITY")
    print("="*80)
    
    research_results = state.get('research_results', [])
    print(f"Current research results: {len(research_results)}")
    llm = get_llm()
    
    evaluation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a quality assurance specialist for an insurance advocacy service.
Your job is to evaluate if a response to an insurance-related email needs additional research before sending.

Review the original email, the current draft response, and evaluate if there are specific gaps in information that would benefit from additional research.

Output ONLY one of these exact labels:
- SEND_RESPONSE - The response is comprehensive and addresses all key points in the email
- NEEDS_RESEARCH - The response has gaps or missing information that require additional research"""),
        ("human", """Original email:
{email_content}

Current draft response:
{response}

Current research cycle: {cycle_num}

Does this response need additional research before sending? Answer with ONLY the label.""")
    ])
    
    chain = evaluation_prompt | llm | StrOutputParser()
    evaluation = chain.invoke({
        "email_content": email_content,
        "response": response,
        "cycle_num": state.get('research_cycles', 0)
    }).strip()
    
    print(f"Response evaluation result: {evaluation}")
    
    if "NEEDS_RESEARCH" in evaluation:
        state['research_cycles'] = state.get('research_cycles', 0) + 1
        state['needs_more_research'] = True
        
        research_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze the email and current response to identify specific gaps in information.
Generate up to 2 additional search queries that would help fill these gaps.
Format your response as a JSON list of query strings.
Example: ["specific query 1", "specific query 2"]"""),
            ("human", """Original email:
{email_content}

Current draft response:
{response}

What specific information is missing? Generate focused search queries to fill these gaps.""")
        ])
        
        try:
            chain = research_prompt | llm | StrOutputParser()
            additional_queries_json = chain.invoke({
                "email_content": email_content,
                "response": response
            })
            additional_queries_json = re.sub(r'^```json', '', additional_queries_json)
            additional_queries_json = re.sub(r'```$', '', additional_queries_json)
            additional_queries_json = additional_queries_json.strip()
            
            try:
                additional_queries = json.loads(additional_queries_json)
                if isinstance(additional_queries, list):
                    additional_queries = additional_queries[:2] 
                else:
                    additional_queries = [additional_queries_json]
                    
                state['additional_queries'] = additional_queries
                print(f"Generated additional queries: {additional_queries}")
            except json.JSONDecodeError as je:
                print(f"Failed to parse additional queries JSON: {additional_queries_json}")
                print(f"JSON error: {je}")
                state['additional_queries'] = [f"specific details about {subject} insurance policy"]
        except Exception as e:
            print(f"Error generating additional queries: {e}")
            state['additional_queries'] = [f"insurance policy details for {subject}"]
        
        print(f"Will perform additional research cycle {state['research_cycles']}")
    else:
        state['needs_more_research'] = False
        print("Response evaluation: Ready to send")
    
    state['needs_evaluation'] = False
    
    print("="*80)
    print("RESPONSE EVALUATION COMPLETE")
    print("="*80 + "\n")
    
    return state

def send_email_response(state: AgentState):
    email = state.get('new_email')
    if not email:
        print("No new email to send a response to.")
        return state
    
    payload = email.get('payload', {})
    headers = payload.get('headers', [])
    sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
    body = get_email_body(payload)
    email_content = f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    if not subject.startswith("Re:"):
        reply_subject = f"Re: {subject}"
    else:
        reply_subject = subject
    
    message_text = state.get('llm_output', '')
    thread_id = email.get('threadId')
    message_id = None
    for header in headers:
        header_name = header.get('name', '').lower()
        if header_name in ['message-id', 'messageid', 'message_id']:
            message_id = header.get('value')
            break
    
    if not message_id and email.get('id'):
        message_id = f"<{email.get('id')}@gmail.com>"
    
    print(f"\n{'='*80}")
    print(f"SENDING EMAIL RESPONSE")
    print(f"{'='*80}")
    print(f"To: {sender}")
    print(f"Subject: {reply_subject}")
    print(f"Thread ID: {thread_id}")
    print(f"In reply to message ID: {message_id}")
    print(f"{'='*80}")
    print(f"Message preview: {message_text[:200]}...")
    print(f"{'='*80}\n")
    
    send_email(
        service=service, 
        to=sender, 
        subject=reply_subject, 
        message_text=message_text,
        thread_id=thread_id,
        message_id=message_id
    )
    
    print(f"\n{'='*80}")
    print(f"EXTRACTING AND STORING MEMORY")
    print(f"{'='*80}")
    
    from my_agent.utils.tools import extract_and_store_memory
    
    try:
        research_results = state.get('research_results', [])
        
        memory_id = extract_and_store_memory(
            email_content=email_content, 
            search_results=research_results, 
            response=message_text
        )
        
        if memory_id:
            print(f"[Memory] Successfully stored conversation memory with ID: {memory_id}")
            if 'debug' not in state:
                state['debug'] = {}
            state['debug']['memory_stored'] = True
            state['debug']['memory_id'] = memory_id
            
            if 'stored_memories' not in state:
                state['stored_memories'] = []
            state['stored_memories'].append(memory_id)
        else:
            print("[Memory] Failed to store conversation memory")
            if 'debug' not in state:
                state['debug'] = {}
            state['debug']['memory_stored'] = False
            
    except Exception as e:
        import traceback
        print(f"[Memory] Error storing memory: {e}")
        print(traceback.format_exc())
        if 'debug' not in state:
            state['debug'] = {}
        state['debug']['memory_error'] = str(e)
    
    print(f"{'='*80}")
    print(f"MEMORY EXTRACTION COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"Email sent in response to: {subject}, and state updated.")
    return state
        
def flag_email(state: AgentState):
    email = state.get('new_email')
    if not email:
        print("No email to flag.")
        return state
    
    email_id = email['id']
    classification_raw = state.get('email_classification')
    if classification_raw is None:
        print("No classification found, defaulting to 'Non-Insurance'")
        classification = 'no'
    else:
        classification = str(classification_raw).lower()
    
    if classification == 'no':
        label_name = 'Non-Insurance'
    elif classification == 'yes':
        label_name = 'Insurance'
    else:
        print(f"Unexpected classification value: {classification_raw}, defaulting to 'Non-Insurance'")
        label_name = 'Non-Insurance'

        state['new_email'] = None
        if 'processed_email_ids' not in state:
            state['processed_email_ids'] = []
        
        if email_id not in state['processed_email_ids']:
            state['processed_email_ids'].append(email_id)
            print(f"Added email ID {email_id} to processed list")
        
        print(f"Email {email_id} processed without Gmail API interaction. State updated.")
        return state
    
    try:
        label_id = get_or_create_label(service, label_name)
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={
                'addLabelIds': [label_id],
                'removeLabelIds': []
            }
        ).execute()
        print(f"Email labeled as '{label_name}'")
    except Exception as e:
        print(f"Error adding label to email: {e}")
    
    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={
                'removeLabelIds': ['UNREAD']
            }
        ).execute()
        print(f"Email marked as read (UNREAD label removed)")
    except Exception as e:
        print(f"Error marking email as read: {e}")
    
    state['new_email'] = None
    if 'processed_email_ids' not in state:
        state['processed_email_ids'] = []
    
    if email_id not in state['processed_email_ids']:
        state['processed_email_ids'].append(email_id)
        print(f"Added email ID {email_id} to processed list")
    
    print(f"Email {email_id} flagged and marked as read. State updated.")
    return state

def response_evaluation_router(state: AgentState):
    if state.get('research_cycles', 0) >= 2: 
        print("Maximum research cycles reached. Proceeding with current response.")
        state['needs_more_research'] = False
        state['needs_evaluation'] = False  
        return 'send_response'
    

    routing_from_generate_response = state.get('needs_evaluation', False)
    routing_from_evaluate = not state.get('needs_evaluation', True) and state.get('needs_more_research') is not None
    if routing_from_generate_response:
        return 'evaluate'
    
    if routing_from_evaluate:
        if state.get('needs_more_research', False):
            return 'research'
        else:
            return 'send_response'
    
    print("Warning: Ambiguous routing state. Defaulting to send_response.")
    return 'send_response'

def email_polling_router(state: AgentState):
    if state.get('new_email'):
        print("New email found, proceeding to classification")
        return 'classify_email'
    
    if state.get('continue_polling', False):
        print("Waiting before next email check...")
        return 'check_emails'
    
    print("Email polling complete, no new emails found")
    return '__end__'

def send_confirmed_email(draft_data):
    try:
        to = draft_data.get('to')
        subject = draft_data.get('subject')
        message_text = draft_data.get('message_text')
        thread_id = draft_data.get('thread_id')
        message_id = draft_data.get('message_id')
        
        print(f"\n{'='*80}")
        print(f"SENDING CONFIRMED EMAIL RESPONSE")
        print(f"{'='*80}")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Thread ID: {thread_id}")
        print(f"{'='*80}\n")
        
        if not service:
            return {
                "success": False,
                "error": "Gmail service not initialized"
            }
        
        send_email(
            service=service, 
            to=to, 
            subject=subject, 
            message_text=message_text,
            thread_id=thread_id,
            message_id=message_id
        )
        
        return {
            "success": True,
            "message": f"Email sent successfully to {to}"
        }
        
    except Exception as e:
        import traceback
        print(f"Error sending confirmed email: {e}")
        print(traceback.format_exc())
        
        return {
            "success": False,
            "error": str(e)
        }
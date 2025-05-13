from typing import TypedDict, List, Dict, Optional, Any

class AgentState(TypedDict, total=False):
    """Type definition for the agent's state"""
    initialized: bool
    new_email: Optional[Dict[str, Any]]
    email_classification: str
    llm_output: str
    processed_email_ids: List[str]
    error: str
    messages: List[Dict[str, Any]]
    research_results: List[Dict[str, Any]]
    memory_context: str
    stored_memories: List[str]
    debug: Dict[str, Any] 
    research_cycles: int 
    needs_evaluation: bool
    needs_more_research: bool 
    additional_queries: List[str]
    polling_cycle: int 
    continue_polling: bool 

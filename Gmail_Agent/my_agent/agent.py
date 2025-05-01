from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from my_agent.utils.nodes import check_for_new_emails, classify_email, generate_response
from my_agent.utils.nodes import send_email_response, flag_email, new_email_router
from my_agent.utils.nodes import classification_router, agent, research, memory_injection
from my_agent.utils.nodes import evaluate_response_quality, response_evaluation_router
from my_agent.utils.nodes import email_polling_router
from my_agent.utils.state import AgentState
import json

workflow = StateGraph(AgentState)

workflow.add_node('agent', agent)
workflow.add_node('check_emails', check_for_new_emails)
workflow.add_node('classify_email', classify_email)
workflow.add_node('memory_injection', memory_injection)
workflow.add_node('generate_response', generate_response)
workflow.add_node('evaluate', evaluate_response_quality)
workflow.add_node('research', research)
workflow.add_node('send_response', send_email_response)
workflow.add_node('flag_email', flag_email)

workflow.add_conditional_edges('check_emails', email_polling_router, {
    'classify_email': 'classify_email',
    'check_emails': 'check_emails', 
    '__end__': END
})

workflow.add_conditional_edges('classify_email', classification_router, {
    'research': 'research',
    'flag_email': 'flag_email'
})

workflow.add_conditional_edges('generate_response', response_evaluation_router, {
    'evaluate': 'evaluate',
    'send_response': 'send_response'
})

workflow.add_conditional_edges('evaluate', response_evaluation_router, {
    'evaluate': 'evaluate',
    'research': 'research',
    'send_response': 'send_response'
})

workflow.add_edge('agent', 'check_emails')
workflow.add_edge('research', 'memory_injection')
workflow.add_edge('memory_injection', 'generate_response')
workflow.add_edge('send_response', 'flag_email')
workflow.add_edge('flag_email', 'check_emails') 
workflow.set_entry_point('agent')

print("""
Initialized Insurance Agent with Memory Capabilities:
- Continuous Email Polling: Repeatedly checks for new emails
- Email Classification: Determines if emails are insurance-related
- Memory Injection: Retrieves relevant past information for context
- Research: Searches for up-to-date insurance information with adaptive cycles
- Response Generation: Creates professional responses with memory context
- Response Evaluation: Evaluates if additional research cycles are needed
- Memory Extraction: Stores important conversation details for future use
""")

graph = workflow.compile()


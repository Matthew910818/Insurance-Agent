// Agent workflow definition
import { StateGraph } from 'langgraph/graph';
import { END } from 'langgraph/graph';
import { check_for_new_emails, classify_email, generate_response, 
         send_email_response, flag_email, new_email_router,
         classification_router, agent, research, memory_injection,
         evaluate_response_quality, response_evaluation_router, 
         email_polling_router } from './utils/nodes.js';
import { AgentState } from './utils/state.js';

// Initialize the workflow
const workflow = new StateGraph({ name: "Gmail Agent", stateType: AgentState });

// Add nodes
workflow.addNode("agent", agent);
workflow.addNode("check_emails", check_for_new_emails);
workflow.addNode("classify_email", classify_email);
workflow.addNode("memory_injection", memory_injection);
workflow.addNode("generate_response", generate_response);
workflow.addNode("evaluate", evaluate_response_quality);
workflow.addNode("research", research);
workflow.addNode("send_response", send_email_response);
workflow.addNode("flag_email", flag_email);

// Add conditional edges
workflow.addConditionalEdges(
  "check_emails",
  email_polling_router,
  {
    "classify_email": "classify_email",
    "check_emails": "check_emails",
    "__end__": END
  }
);

workflow.addConditionalEdges(
  "classify_email",
  classification_router,
  {
    "research": "research",
    "flag_email": "flag_email"
  }
);

workflow.addConditionalEdges(
  "generate_response",
  response_evaluation_router,
  {
    "evaluate": "evaluate",
    "send_response": "send_response"
  }
);

workflow.addConditionalEdges(
  "evaluate",
  response_evaluation_router,
  {
    "evaluate": "evaluate",
    "research": "research",
    "send_response": "send_response"
  }
);

// Add regular edges
workflow.addEdge("agent", "check_emails");
workflow.addEdge("research", "memory_injection");
workflow.addEdge("memory_injection", "generate_response");
workflow.addEdge("send_response", "flag_email");
workflow.addEdge("flag_email", "check_emails");

// Set entry point
workflow.setEntryPoint("agent");

console.log(`
Initialized Insurance Agent with Memory Capabilities:
- Continuous Email Polling: Repeatedly checks for new emails
- Email Classification: Determines if emails are insurance-related
- Memory Injection: Retrieves relevant past information for context
- Research: Searches for up-to-date insurance information with adaptive cycles
- Response Generation: Creates professional responses with memory context
- Response Evaluation: Evaluates if additional research cycles are needed
- Memory Extraction: Stores important conversation details for future use
`);

// Compile the graph
export const graph = workflow.compile(); 
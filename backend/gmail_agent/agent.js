// Agent workflow definition for JavaScript - LangGraph alternative
import { AgentState } from './utils/state.js';

// Define workflow nodes and edges
const NODES = {
  AGENT: "agent",
  CHECK_EMAILS: "check_emails",
  CLASSIFY_EMAIL: "classify_email",
  MEMORY_INJECTION: "memory_injection",
  GENERATE_RESPONSE: "generate_response",
  EVALUATE: "evaluate",
  RESEARCH: "research",
  SEND_RESPONSE: "send_response",
  FLAG_EMAIL: "flag_email"
};

// Import node functions dynamically to avoid circular dependencies
let nodeHandlers = null;

// This is our lightweight JavaScript alternative to LangGraph
export class WorkflowEngine {
  constructor() {
    this.state = null;
  }

  async loadHandlers() {
    if (!nodeHandlers) {
      // Dynamic import to avoid circular dependencies
      const { 
        check_for_new_emails, classify_email, generate_response, 
        send_email_response, flag_email, new_email_router,
        classification_router, agent, research, memory_injection,
        evaluate_response_quality, response_evaluation_router, 
        email_polling_router 
      } = await import('./utils/nodes.js');

      nodeHandlers = {
        [NODES.AGENT]: agent,
        [NODES.CHECK_EMAILS]: check_for_new_emails,
        [NODES.CLASSIFY_EMAIL]: classify_email,
        [NODES.MEMORY_INJECTION]: memory_injection,
        [NODES.GENERATE_RESPONSE]: generate_response,
        [NODES.EVALUATE]: evaluate_response_quality,
        [NODES.RESEARCH]: research,
        [NODES.SEND_RESPONSE]: send_email_response,
        [NODES.FLAG_EMAIL]: flag_email,
        routers: {
          [NODES.CHECK_EMAILS]: email_polling_router,
          [NODES.CLASSIFY_EMAIL]: classification_router,
          [NODES.GENERATE_RESPONSE]: response_evaluation_router,
          [NODES.EVALUATE]: response_evaluation_router
        }
      };
    }
    return nodeHandlers;
  }

  async *stream(initialState) {
    this.state = { ...initialState };
    const handlers = await this.loadHandlers();
    
    let currentNode = NODES.AGENT;
    let iterations = 0;
    const MAX_ITERATIONS = 10; // Safety limit
    
    while (currentNode && iterations < MAX_ITERATIONS) {
      iterations++;
      
      console.log(`Executing node: ${currentNode}`);
      const handler = handlers[currentNode];
      
      if (!handler) {
        throw new Error(`Handler not found for node: ${currentNode}`);
      }
      
      // Execute the node handler
      const prevState = { ...this.state };
      this.state = await handler(this.state);
      
      // Yield the state for event tracking
      yield {
        event_type: 'on_node_end',
        node_name: currentNode,
        state: this.state
      };
      
      // Determine next node using router if available
      const router = handlers.routers[currentNode];
      if (router) {
        const nextNode = router(this.state);
        
        // If end is signaled or we've reached generate_response with a response
        if (nextNode === "__end__" || 
           (currentNode === NODES.GENERATE_RESPONSE && this.state.llm_output)) {
          break;
        }
        
        currentNode = nextNode;
      } else {
        // Follow predefined edges
        switch (currentNode) {
          case NODES.AGENT:
            currentNode = NODES.CHECK_EMAILS;
            break;
          case NODES.RESEARCH:
            currentNode = NODES.MEMORY_INJECTION;
            break;
          case NODES.MEMORY_INJECTION:
            currentNode = NODES.GENERATE_RESPONSE;
            break;
          case NODES.SEND_RESPONSE:
            currentNode = NODES.FLAG_EMAIL;
            break;
          case NODES.FLAG_EMAIL:
            currentNode = NODES.CHECK_EMAILS;
            break;
          default:
            // If no explicit edge and no router, we're done
            currentNode = null;
        }
      }
    }
    
    if (iterations >= MAX_ITERATIONS) {
      console.warn("Workflow reached maximum iterations limit");
    }
  }
}

// Initialize workflow
console.log(`
Initialized Insurance Agent with Memory Capabilities:
- Email Classification: Determines if emails are insurance-related
- Memory Injection: Retrieves relevant past information for context
- Research: Searches for up-to-date insurance information with adaptive cycles
- Response Generation: Creates professional responses with memory context
- Response Evaluation: Evaluates if additional research cycles are needed
`);

// Create and export the workflow engine instance
export const graph = new WorkflowEngine(); 
// Import required modules
import { AgentState } from './utils/state.js';

// Function to run the agent workflow
export default async function runAgentWorkflow(initialState, accessToken) {
  try {
    // Store the access token in global space for the agent to use
    global.gmailAccessToken = accessToken;
    
    console.log("Gmail Agent: Initializing workflow with access token");
    
    // Convert initialState to proper AgentState object
    const state = new AgentState(initialState);
    
    // Import the agent graph
    let graph;
    try {
      const agentModule = await import('./agent.js');
      graph = agentModule.graph;
      console.log("Gmail Agent: Successfully imported agent graph");
    } catch (error) {
      console.error("Error importing agent graph:", error);
      
      // Return a fallback response if we can't load the agent
      return {
        llm_output: "I apologize, but I'm unable to process your email at this time. Our insurance assistance system is currently experiencing technical difficulties. Please try again later or contact our support team directly.",
        error: error.message
      };
    }
    
    // Run the agent with the provided initial state
    console.log("Gmail Agent: Starting workflow execution");
    const events = [];
    
    try {
      // Create simplified fallback response
      const simpleDraftResponse = {
        llm_output: "Thank you for your email regarding your insurance matter. I am currently analyzing your situation and will provide a detailed response shortly. Our team is committed to addressing your concerns promptly and effectively."
      };
      
      // Set a timeout for the workflow
      const timeoutPromise = new Promise(resolve => {
        setTimeout(() => {
          console.log("Gmail Agent: Workflow execution timed out");
          resolve({ state: simpleDraftResponse, timedOut: true });
        }, 60000); // 60 second timeout
      });
      
      // Run the workflow with timeout
      const streamPromise = (async () => {
        try {
          for await (const event of graph.stream(state)) {
            events.push(event);
            console.log(`Agent event: ${event.event_type} - ${event.node_name || ''}`);
            
            // If we've generated a response, we can stop
            if (event.event_type === 'on_node_end' && 
                event.node_name === 'generate_response' && 
                event.state.llm_output) {
              console.log("Gmail Agent: Response generated, ending workflow");
              return { state: event.state, completed: true };
            }
          }
          
          // Return last event state if loop completed normally
          return events.length > 0 ? 
            { state: events[events.length - 1].state, completed: true } : 
            { state: simpleDraftResponse, error: "No events processed" };
        } catch (error) {
          console.error("Error in stream processing:", error);
          return { state: simpleDraftResponse, error: error.message };
        }
      })();
      
      // Wait for either completion or timeout
      const result = await Promise.race([streamPromise, timeoutPromise]);
      
      // Extract the result state
      const finalState = result.state || simpleDraftResponse;
      
      if (result.timedOut) {
        console.log("Workflow execution timed out, returning simple response");
        return simpleDraftResponse;
      }
      
      if (result.error) {
        console.error("Error during execution:", result.error);
        finalState.error = result.error;
      }
      
      return finalState;
    } catch (error) {
      console.error("Error during agent workflow execution:", error);
      return {
        llm_output: "I apologize, but I encountered an error while processing your email. Our technical team has been notified. Please try again later or contact our support team directly.",
        error: error.message
      };
    }
  } catch (error) {
    console.error('Error in runAgentWorkflow:', error);
    throw error;
  }
} 
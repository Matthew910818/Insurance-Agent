// JavaScript equivalent of the Python AgentState TypedDict
export class AgentState {
  constructor(initialState = {}) {
    this.initialized = initialState.initialized || false;
    this.new_email = initialState.new_email || null;
    this.email_classification = initialState.email_classification || '';
    this.llm_output = initialState.llm_output || '';
    this.processed_email_ids = initialState.processed_email_ids || [];
    this.error = initialState.error || '';
    this.messages = initialState.messages || [];
    this.research_results = initialState.research_results || [];
    this.memory_context = initialState.memory_context || '';
    this.stored_memories = initialState.stored_memories || [];
    this.debug = initialState.debug || {};
    this.research_cycles = initialState.research_cycles || 0;
    this.needs_evaluation = initialState.needs_evaluation || false;
    this.needs_more_research = initialState.needs_more_research || false;
    this.additional_queries = initialState.additional_queries || [];
    this.polling_cycle = initialState.polling_cycle || 0;
    this.continue_polling = initialState.continue_polling || false;
  }
}

// Helper function to create a state object from a plain object
export function createState(obj) {
  return new AgentState(obj);
} 
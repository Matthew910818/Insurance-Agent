#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from utils.tools import WebSearchTool

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please add your OpenAI API key to the .env file.")
        return
    
    print("=" * 80)
    print("Web Search Tool Demo")
    print("=" * 80)
    
    # Create the WebSearchTool
    web_search_tool = WebSearchTool()
    
    # Prompt the user for search queries
    while True:
        # Get user input
        query = input("\nEnter a search query (or 'exit' to quit): ")
        
        # Exit if requested
        if query.lower() in ['exit', 'quit', 'q']:
            break
        
        # Skip empty queries
        if not query.strip():
            continue
        
        print(f"\nSearching for: {query}")
        print("-" * 80)
        
        # Execute the search
        result = web_search_tool._run(query)
        
        # Display the result
        print("\nSearch Results:")
        print("-" * 80)
        print(result)
        print("-" * 80)
    
    print("\nThank you for using the Web Search Tool Demo!")

if __name__ == "__main__":
    main() 
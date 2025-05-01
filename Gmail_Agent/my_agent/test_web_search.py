#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from utils.tools import WebSearchTool

def test_web_search():
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please add your OpenAI API key to the .env file.")
        return False
    
    if openai_api_key == "your_openai_api_key_here":
        print("Error: You need to replace 'your_openai_api_key_here' with your actual OpenAI API key in the .env file.")
        return False
    
    print(f"Using OpenAI API key: {openai_api_key[:4]}...{openai_api_key[-4:]}")
    
    # Create an instance of the WebSearchTool
    web_search_tool = WebSearchTool()
    
    # Test with a simple query that requires web search
    query = "What is the current date today and what are the main headlines in the news?"
    print(f"\nTesting web search with query: '{query}'")
    
    try:
        print("Running web search...")
        result = web_search_tool._run(query)
        
        print("\nSearch Result:")
        print("-" * 80)
        print(result)
        print("-" * 80)
        
        if result and not result.startswith("Error"):
            print("\n✅ Web search tool is working correctly!")
            return True
        else:
            print("\n❌ Web search returned an error response.")
            return False
    except Exception as e:
        print(f"\n❌ Error running web search: {str(e)}")
        import traceback
        print(traceback.format_exc())
        print("\nWeb search tool is NOT working correctly.")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("WebSearchTool Test")
    print("=" * 80)
    
    success = test_web_search()
    
    print("\nTest result:", "PASSED" if success else "FAILED")
    sys.exit(0 if success else 1) 
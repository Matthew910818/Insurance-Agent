#!/usr/bin/env python3
"""
Debug script to test WebSearchTool in isolation.
This emulates how it would be used in LangGraph.
"""
import os
import sys
from utils.tools import WebSearchTool

def main():
    # Print environment info
    print("=" * 80)
    print("WebSearchTool Debug - LangGraph Simulation")
    print("=" * 80)
    print(f"OPENAI_API_KEY is {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    
    # Create a fresh instance of the tool
    web_search_tool = WebSearchTool()
    print("Created WebSearchTool instance")
    
    # Test query
    query = "Who is the current US president of 2025?"
    print(f"\nRunning test query: {query}")
    print("-" * 80)
    
    # Execute the search
    result = web_search_tool._run(query)
    
    # Display the result
    print("\nSearch Results:")
    print("-" * 80)
    print(result)
    print("-" * 80)
    print("\nTest complete")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Debug script to check the memory store in your LangGraph application.
This allows you to verify that memories are being correctly stored and retrieved.
"""
import os
import sys
from dotenv import load_dotenv
from utils.tools import search_memory, get_relevant_memories

def list_memories(query=None, limit=10):
    """
    List all memories or search for specific ones.
    
    Args:
        query: Optional search query string
        limit: Maximum number of memories to return
    """
    print("=" * 80)
    print("MEMORY DEBUG UTILITY")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Check if we are searching or listing all
    if query:
        print(f"Searching memories for: '{query}'")
        memories = search_memory(query, limit=limit)
    else:
        print(f"Listing the most recent {limit} memories:")
        # Use a generic query to get recent items
        memories = search_memory("insurance policy claim denial appeal", limit=limit)
    
    # Display the results
    if not memories:
        print("\nNo memories found.")
    else:
        print(f"\nFound {len(memories)} memories:")
        for i, memory in enumerate(memories, 1):
            print(f"\n--- MEMORY #{i} ---")
            print(f"Content: {memory['content']}")
            print(f"Source: {memory['metadata'].get('source', 'unknown')}")
            if 'timestamp' in memory['metadata']:
                print(f"Timestamp: {memory['metadata']['timestamp']}")
            print(f"Relevance score: {memory.get('relevance_score', 'N/A')}")
    
    print("\n" + "=" * 80)
    return memories

def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Debug memory storage in LangGraph.')
    parser.add_argument('--query', '-q', type=str, help='Search query (optional)')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Maximum number of results (default: 10)')
    parser.add_argument('--formatted', '-f', action='store_true', help='Show formatted memories as they would appear in prompts')
    args = parser.parse_args()
    
    if args.formatted and args.query:
        # Show formatted memories as they would appear in prompts
        print("=" * 80)
        print("FORMATTED MEMORIES (as they would appear in prompts)")
        print("=" * 80)
        formatted_memories = get_relevant_memories(args.query, limit=args.limit)
        print(formatted_memories or "No relevant memories found.")
    else:
        # List memories
        list_memories(args.query, args.limit)

if __name__ == "__main__":
    main() 
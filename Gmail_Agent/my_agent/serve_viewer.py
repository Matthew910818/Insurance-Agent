#!/usr/bin/env python3
"""
A simple HTTP server to serve the memory viewer HTML page.
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Set the directory containing the HTML file
directory = Path(__file__).parent

# Define port
PORT = 8080

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(directory), **kwargs)

def main():
    """Start the server and open the viewer in a browser."""
    print(f"\nStarting Memory Viewer server at http://localhost:{PORT}")
    print(f"Serving files from: {directory}")
    print("\nNOTE: Make sure the API server is also running on port 8000")
    print("To start the API server: python my_agent/api_memory.py")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Check if the HTML file exists
    html_path = directory / "memory_viewer.html"
    if not html_path.exists():
        print(f"ERROR: Memory viewer HTML file not found at {html_path}")
        return
    
    # Open the browser
    webbrowser.open(f"http://localhost:{PORT}/memory_viewer.html")
    
    # Start the server
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server")
            httpd.shutdown()

if __name__ == "__main__":
    main() 
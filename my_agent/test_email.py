#!/usr/bin/env python3
"""
Test script to check Gmail API connection and list available emails
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_gmail_service():
    # Load credentials from environment variables or use defaults
    client_secrets = os.getenv("GMAIL_CLIENT_SECRETS", "credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")
    
    print(f"Looking for credentials at: {client_secrets}")
    print(f"Looking for token at: {token_file}")
    
    # Check if files exist
    if not os.path.exists(client_secrets):
        print(f"ERROR: Client secrets file not found at {client_secrets}")
        return None
        
    if not os.path.exists(token_file):
        print(f"ERROR: Token file not found at {token_file}")
        print("Please run authenticate.py first")
        return None
    
    try:
        # Load credentials
        creds = Credentials.from_authorized_user_file(token_file, ["https://mail.google.com/"])
        
        # Check if credentials expired
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            # Save refreshed credentials
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
                print("Token refreshed and saved")
                
        # Build service
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        print(f"ERROR initializing Gmail API service: {str(e)}")
        return None

def list_labels(service):
    print("\n=== Gmail Labels ===")
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    
    if not labels:
        print("No labels found.")
    else:
        print(f"Found {len(labels)} labels:")
        for label in labels:
            print(f" - {label['name']} (ID: {label['id']})")

def list_messages(service, max_results=5):
    print(f"\n=== Recent {max_results} Gmail Messages ===")
    
    # Get messages from inbox
    results = service.users().messages().list(
        userId='me', 
        labelIds=['INBOX'], 
        maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    
    if not messages:
        print("No messages found.")
        return
        
    print(f"Found {len(messages)} messages:")
    
    # Get message details
    for i, message in enumerate(messages, 1):
        msg = service.users().messages().get(
            userId='me', 
            id=message['id'], 
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown date')
        
        print(f"{i}. ID: {message['id']}")
        print(f"   From: {from_email}")
        print(f"   Subject: {subject}")
        print(f"   Date: {date}")
        print(f"   Labels: {msg.get('labelIds', [])}")
        print()

def main():
    print("=== Gmail API Test ===")
    
    # Get Gmail service
    service = get_gmail_service()
    if not service:
        print("Failed to initialize Gmail service")
        return
        
    print("Gmail service initialized successfully!")
    
    # Test operations
    list_labels(service)
    list_messages(service, max_results=10)
    
    print("\nTest complete!")

if __name__ == "__main__":
    main() 
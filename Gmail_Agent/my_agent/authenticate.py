import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import sys

SCOPES = ['https://mail.google.com/']

def main():
    credentials_path = os.environ.get('GMAIL_CLIENT_SECRETS', 'credentials.json')
    token_path = os.environ.get('GMAIL_TOKEN_FILE', 'token.json')
    
    print(f"Looking for credentials at: {os.path.abspath(credentials_path)}")
    print(f"Looking for token at: {os.path.abspath(token_path)}")
    print(f"Do files exist? credentials: {os.path.exists(credentials_path)}, token: {os.path.exists(token_path)}")
    
    if not os.path.exists(credentials_path):
        print(f"Error: {credentials_path} not found!")
        print("\nPlease download your credentials.json file from the Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project and enable the Gmail API")
        print("3. Create OAuth credentials (Desktop application)")
        print("4. Download the credentials and save as credentials.json")
        return

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_info(
            json.loads(open(token_path).read()), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"\nAuthentication successful! Token saved to {token_path}")
    else:
        print("\nExisting valid credentials found. You're already authenticated.")

    print("\nYou can now use the Gmail API in your application.")

if __name__ == '__main__':
    import json
    try:
        main()
    except Exception as e:
        print(f"Error during authentication: {str(e)}") 
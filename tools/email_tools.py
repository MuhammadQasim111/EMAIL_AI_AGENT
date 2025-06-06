# agents-sdk-course-2/email-agent/tools/email_tools.py

import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from typing import List, Dict, Any, Optional

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# --- Gmail API Integration Functions ---

def get_gmail_service():
    """
    Authenticates with Gmail API and returns a service object.
    The `token.json` file stores the user's access and refresh tokens,
    and is created automatically when the authorization flow completes for the first time.
    """
    creds = None
    # Always use the project root for credentials and token files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cred_path = os.path.join(base_dir, 'credentials.json')
    token_path = os.path.join(base_dir, 'token.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=8082)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred during Gmail service creation: {error}')
        return None
def create_message(sender: str, to: str, subject: str, message_text: str) -> dict:
    """
    Create a message for email sending.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_gmail_message(service, sender: str, to: str, subject: str, message_text: str):
    """
    Send an email message using the Gmail API.
    """
    try:
        message = create_message(sender, to, subject, message_text)
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        print(f'Message Id: {sent_message["id"]}')
        return sent_message
    except HttpError as error:
        print(f'An error occurred during email sending to {to}: {error}')
        return None
def read_recipients_from_excel(file_path: str) -> List[Dict[str, str]]:
    """
    Reads recipient emails from an Excel file.
    Assumes the Excel file has a column named 'Email' (case-insensitive).
    Returns a list of dictionaries, where each dict might contain 'email' and optionally 'name'.
    """
    try:
        df = pd.read_excel(file_path)
        recipients = []
        # Find the email column, case-insensitively
        email_col = None
        for col in df.columns:
            if col.lower() == 'email':
                email_col = col
                break
        if not email_col:
            raise ValueError("Excel file must contain an 'Email' column.")
        for _, row in df.iterrows():
            recipient_data = {}
            if email_col in row and pd.notna(row[email_col]):
                recipient_data['email'] = str(row[email_col]).strip()
                # Optionally, try to get a 'Name' column if it exists
                if 'Name' in df.columns and pd.notna(row['Name']):
                    recipient_data['name'] = str(row['Name']).strip()
                recipients.append(recipient_data)
        # Limit to maximum 10 emails as per requirement
        return recipients[:500]
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []
    
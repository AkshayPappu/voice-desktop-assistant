from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import os
import pickle
from datetime import datetime, timedelta
import re

class EmailHandler:
    def __init__(self):
        """Initialize the Gmail API client"""
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                      'https://www.googleapis.com/auth/gmail.send',
                      'https://www.googleapis.com/auth/gmail.modify']
        self.creds = None
        self.service = None
        # Get the server directory path
        self.server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API"""
        try:
            # Check if we have stored credentials
            token_path = os.path.join(self.server_dir, 'token.pickle')
            credentials_path = os.path.join(self.server_dir, 'credentials.json')
            
            # Verify credentials file exists
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"credentials.json not found in {self.server_dir}. "
                    "Please place your OAuth2 credentials file there."
                )

            # Try to load existing token
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    self.creds = pickle.load(token)

            # If no valid credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    print("Refreshing expired credentials...")
                    self.creds.refresh(Request())
                else:
                    print("Starting new authentication flow...")
                    print("A browser window will open. Please sign in with your Gmail account (akshaypap2005@gmail.com)")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, 
                        self.SCOPES,
                        redirect_uri='http://localhost'  # Match the redirect URI in credentials
                    )
                    self.creds = flow.run_local_server(
                        port=0,
                        prompt='consent',  # Force consent screen to ensure correct account
                        authorization_prompt_message='Please sign in with akshaypap2005@gmail.com'
                    )
                
                # Save the credentials for the next run
                with open(token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
                print("Authentication successful! Credentials saved.")

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            
            # Verify we can access the account
            profile = self.service.users().getProfile(userId='me').execute()
            print(f"Successfully authenticated as: {profile['emailAddress']}")
            
            if profile['emailAddress'] != 'akshaypap2005@gmail.com':
                print(f"Warning: Authenticated as {profile['emailAddress']}, not akshaypap2005@gmail.com")
                print("Please delete token.pickle and try again, making sure to select the correct account.")
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            if "invalid_grant" in str(e).lower():
                print("Token is invalid. Please delete token.pickle and try again.")
            elif "invalid_client" in str(e).lower():
                print("Invalid client credentials. Please check your credentials.json file.")
            raise

    def get_recent_emails(self, max_results=10, days_back=7, important_only=False):
        """
        Get recent emails from inbox
        
        Args:
            max_results (int): Maximum number of emails to retrieve
            days_back (int): Number of days to look back
            important_only (bool): Whether to only return important emails
            
        Returns:
            list: List of email objects with subject, sender, date, and snippet
        """
        try:
            if not self.service:
                raise Exception("Gmail service not initialized. Authentication may have failed.")
                
            # Calculate date range
            date_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Build query
            query = f'after:{date_after}'
            if important_only:
                query += ' is:important'
            
            print(f"Fetching emails with query: {query}")
            
            # Get messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg['payload']['headers']
                email_data = {
                    'id': message['id'],
                    'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)'),
                    'sender': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                    'snippet': msg.get('snippet', '')
                }
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            if "invalid_grant" in str(e).lower():
                print("Token has expired. Please delete token.pickle and authenticate again.")
            return []

    def get_email_content(self, email_id):
        """
        Get full content of an email
        
        Args:
            email_id (str): ID of the email to retrieve
            
        Returns:
            str: Full content of the email
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            if 'payload' not in message:
                return "No content found"
                
            payload = message['payload']
            if 'parts' in payload:
                parts = payload['parts']
                content = ''
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            content += base64.urlsafe_b64decode(data).decode()
                return content
            elif 'body' in payload and 'data' in payload['body']:
                return base64.urlsafe_b64decode(payload['body']['data']).decode()
            
            return "No readable content found"
            
        except Exception as e:
            print(f"Error fetching email content: {str(e)}")
            return "Error retrieving email content"

    def draft_email(self, to, subject, body):
        """
        Draft a new email
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            dict: Draft email data
        """
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            msg = MIMEText(body)
            message.attach(msg)
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw}}
            ).execute()
            
            return {
                'id': draft['id'],
                'message': {
                    'to': to,
                    'subject': subject,
                    'snippet': body[:100] + '...' if len(body) > 100 else body
                }
            }
            
        except Exception as e:
            print(f"Error drafting email: {str(e)}")
            return None

    def send_email(self, to, subject, body):
        """
        Send an email immediately
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            dict: Sent email data
        """
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            msg = MIMEText(body)
            message.attach(msg)
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            return {
                'id': sent['id'],
                'message': {
                    'to': to,
                    'subject': subject,
                    'snippet': body[:100] + '...' if len(body) > 100 else body
                }
            }
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return None

    def search_emails(self, query, max_results=10):
        """
        Search emails using Gmail's search syntax
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of matching emails
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg['payload']['headers']
                email_data = {
                    'id': message['id'],
                    'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)'),
                    'sender': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                    'snippet': msg.get('snippet', '')
                }
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error searching emails: {str(e)}")
            return [] 
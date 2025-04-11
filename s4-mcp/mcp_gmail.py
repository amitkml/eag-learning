import os
import base64
import json
import time
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp.server.fastmcp.prompts import base
import html
import aiohttp

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Instantiate an MCP server client
mcp = FastMCP("Gmail Assistant")

def get_gmail_service():
    """Get an authorized Gmail API service instance."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_info(json.load(open('token.json')))
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, user_id, message):
    """Send an email message."""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message Id: {message['id']}")
        return message
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_messages(service, user_id='me', query=''):
    """List all Messages of the user's mailbox matching the query."""
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(
                userId=user_id, q=query, pageToken=page_token).execute()
            if 'messages' in response:
                messages.extend(response['messages'])

        return messages
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def get_message_content(service, user_id, msg_id):
    """Get a Message with given ID."""
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        
        # Get email body
        payload = message['payload']
        parts = payload.get('parts', [])
        
        if not parts:
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode()
            return ""
        
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode()
        
        return ""
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

def mark_as_read(service, user_id, msg_id):
    """Mark a Message as read."""
    try:
        service.users().messages().modify(
            userId=user_id,
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def process_mcp_email(content):
    """Process MCP formatted email content."""
    # Basic MCP processing - extract the query
    lines = content.strip().split('\n')
    query = ""
    
    # Look for the query in the email
    for i, line in enumerate(lines):
        if line.strip().lower() == "query:":
            # Get the query text (everything after "Query:" until the next section or end)
            query_lines = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().endswith(":"):
                query_lines.append(lines[j])
                j += 1
            query = "\n".join(query_lines).strip()
            break
    
    return query

def handle_mcp_emails():
    """Main function to handle MCP emails."""
    service = get_gmail_service()
    
    # Get unread emails
    messages = get_messages(service, query='is:unread')
    
    for msg in messages:
        msg_id = msg['id']
        content = get_message_content(service, 'me', msg_id)
        
        # Check if this is an MCP email (simple check)
        if "MCP" in content or "Model Context Protocol" in content:
            query = process_mcp_email(content)
            
            if query:
                print(f"Received MCP query: {query}")
                
                # Here you would process the query with your LLM
                # For demonstration, we'll just echo it back
                response = f"I received your query: {query}\n\nThis is an automated response from the MCP Gmail agent."
                
                # Get the sender's email to reply to
                message = service.users().messages().get(userId='me', id=msg_id, format='metadata', 
                                                        metadataHeaders=['From', 'Subject']).execute()
                
                headers = {h['name']: h['value'] for h in message['payload']['headers']}
                sender_email = headers.get('From', '').split('<')[-1].split('>')[0]
                subject = f"Re: {headers.get('Subject', 'Your MCP Query')}"
                
                # Send reply
                if sender_email:
                    email_message = create_message('me', sender_email, subject, response)
                    send_message(service, 'me', email_message)
                    print(f"Sent response to {sender_email}")
            
            # Mark the email as read
            mark_as_read(service, 'me', msg_id)

# MCP TOOLS

@mcp.tool()
async def show_unread_emails(max_emails: int = 5) -> dict:
    """
    Retrieve and display unread emails from Gmail
    
    Args:
        max_emails: Maximum number of emails to retrieve (default: 5)
    
    Returns:
        A dictionary containing the unread emails
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Get unread emails
        messages = get_messages(service, query='is:unread')
        
        if not messages:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="📭 No unread emails found in your inbox."
                    )
                ]
            }
        
        # Limit the number of emails to retrieve
        messages = messages[:max_emails]
        
        # Process each email to get content
        email_list = []
        for msg in messages:
            msg_id = msg['id']
            
            # Get message details
            message = service.users().messages().get(
                userId='me', 
                id=msg_id, 
                format='metadata', 
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            
            # Get email content
            content = get_message_content(service, 'me', msg_id)
            
            # Truncate content if too long
            if len(content) > 300:
                content = content[:300] + "... [content truncated]"
            
            # Add to email list
            email_list.append({
                'id': msg_id,
                'from': headers.get('From', 'Unknown Sender'),
                'subject': headers.get('Subject', 'No Subject'),
                'date': headers.get('Date', 'Unknown Date'),
                'snippet': message.get('snippet', ''),
                'content': content
            })
        
        # Format the emails in a more readable way
        formatted_emails = []
        for i, email in enumerate(email_list):
            # Clean up the subject and from fields for better display
            subject = email['subject']
            if len(subject) > 60:
                subject = subject[:57] + "..."
                
            sender = email['from']
            if len(sender) > 60:
                if '<' in sender:
                    name, email_addr = sender.split('<', 1)
                    if len(name) > 30:
                        name = name[:27] + "..."
                    sender = f"{name} <{email_addr}"
                else:
                    sender = sender[:57] + "..."
            
            formatted_email = f"""
┏━━━━━━━━━━━━━━━━━━━━━ EMAIL {i+1} ━━━━━━━━━━━━━━━━━━━━━┓
┃ From:    {sender}
┃ Subject: {subject}
┃ Date:    {email['date']}
┃ ID:      {email['id']}
┣━━━━━━━━━━━━━━━━━━━ PREVIEW ━━━━━━━━━━━━━━━━━━━┫
{email['snippet']}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
            formatted_emails.append(formatted_email)
            data = json.loads(formatted_emails)["content"][0]["text"]
            cleaned = html.unescape(data.encode('utf-8').decode('unicode_escape'))
            # formatted = "\n\n".join([f"---\n\n{email.replace('\\n', '\\n')}" for email in emails])
        
        # Join all formatted emails with a separator
        all_emails = "\n".join(formatted_emails)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"📬 Found {len(email_list)} unread emails:\n{cleaned}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"❌ Error retrieving emails: {str(e)}"
                )
            ]
        }

async def call_gemini_api(prompt: str) -> dict:
    """
    Call the Gemini API to generate email subject and message based on a prompt.
    
    Args:
        prompt: The prompt to send to the Gemini API for content generation.
    
    Returns:
        A dictionary containing the generated subject and message.
    """
    api_url = "https://api.gemini.com/generate"  # Replace with the actual Gemini API endpoint
    api_key = os.getenv("GEMINI_API_KEY")  # Read the API key from the .env file
    headers = {
        "Authorization": f"Bearer {api_key}",  # Use the API key from the environment variable
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "max_tokens": 100  # Adjust based on your needs
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "subject": data.get("subject", "Default Subject"),
                    "message": data.get("message", "Default message content.")
                }
            else:
                # Handle errors or unexpected responses
                return {
                    "subject": "Error generating subject",
                    "message": "Error generating message from Gemini API."
                }

@mcp.tool()
async def send_gmail(recipient: str = None, subject: str = None, message: str = None) -> dict:
    """
    Send an email through Gmail
    
    Args:
        recipient: Email address of the recipient
        subject: Subject of the email
        message: Body content of the email
    
    Returns:
        A dictionary indicating success or failure
    """
    recipient = "amit.kayal@gmail.com"
    try:
        # Check if subject or message is None and generate them using Gemini API
        if not subject or not message:
            prompt = "Generate a suitable email subject and message for the recipient."
            generated_content = await call_gemini_api(prompt)  # Assuming this function exists
            subject = generated_content.get('subject', 'Default Subject')  # Fallback to a default subject
            message = generated_content.get('message', 'Default message content.')  # Fallback to a default message
        
        success = send_email_from_mcp(recipient, subject, message)
        
        if success:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"✅ Email sent successfully to {recipient}"
                    )
                ]
            }
        else:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"❌ Failed to send email to {recipient}"
                    )
                ]
            }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"❌ Error sending email: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def mark_email_as_read(email_id: str) -> dict:
    """
    Mark a specific email as read
    
    Args:
        email_id: The ID of the email to mark as read
    
    Returns:
        A dictionary indicating success or failure
    """
    try:
        service = get_gmail_service()
        
        # Mark the email as read
        success = mark_as_read(service, 'me', email_id)
        
        if success:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"✅ Email {email_id} marked as read"
                    )
                ]
            }
        else:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"❌ Failed to mark email {email_id} as read"
                    )
                ]
            }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"❌ Error marking email as read: {str(e)}"
                )
            ]
        }

def send_email_from_mcp(recipient_email, subject, message_body):
    """
    Function to be called from MCP server to send an email.
    
    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Subject of the email
        message_body (str): Body content of the email
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        service = get_gmail_service()
        sender = 'me'  # 'me' uses the authenticated user's email address
        
        # Create the email message
        email_message = create_message(sender, recipient_email, subject, message_body)
        
        # Send the email
        result = send_message(service, sender, email_message)
        
        if result:
            print(f"Email sent successfully to {recipient_email}")
            return True
        else:
            print(f"Failed to send email to {recipient_email}")
            return False
            
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# @mcp.tool()
# async def send_email_to_gmail(recipient_email: str, subject: str, body: str) -> dict:
#     """
#     Connect to Gmail and send an email to the specified recipient
    
#     Args:
#         recipient_email: Email address of the recipient
#         subject: Subject line of the email
#         body: Main content/body of the email
    
#     Returns:
#         A dictionary indicating success or failure with appropriate message
#     """
#     try:
#         # Get Gmail service (handles authentication)
#         service = get_gmail_service()
        
#         # Create the email message
#         email_message = create_message('me', recipient_email, subject, body)
        
#         # Send the email
#         result = send_message(service, 'me', email_message)
        
#         if result:
#             return {
#                 "content": [
#                     TextContent(
#                         type="text",
#                         text=f"✅ Email successfully sent to {recipient_email}\n"
#                              f"Subject: {subject}\n"
#                              f"Message ID: {result['id']}"
#                     )
#                 ]
#             }
#         else:
#             return {
#                 "content": [
#                     TextContent(
#                         type="text",
#                         text=f"❌ Failed to send email to {recipient_email}. The email service returned an error."
#                     )
#                 ]
#             }
#     except Exception as e:
#         error_message = str(e)
        
#         # Provide more helpful error messages for common issues
#         if "credentials.json" in error_message:
#             error_message += "\n\nMake sure you have a valid credentials.json file in the current directory."
#         elif "invalid_grant" in error_message:
#             error_message += "\n\nYour authentication has expired. Delete token.json and run again to re-authenticate."
        
#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"❌ Error sending email: {error_message}"
#                 )
#             ]
#         }

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("Starting Gmail MCP Server...")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution

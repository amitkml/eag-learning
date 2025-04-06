How to Use This Script
- Set up Google API credentials:
    - Go to the Google Cloud Console
    - Create a new project
    - Enable the Gmail API
    - Create OAuth 2.0 credentials (Desktop application)
    - Download the credentials as credentials.json and place it in the same directory as this script
- Install required packages:
    -    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
- Run the script:
    - python mcp_gmail.py
- First-time authentication:
        - The first time you run the script, it will open a browser window asking you to authorize the application
        - After authorization, a token.json file will be created for future use
- Testing:
        - Send an email to your Gmail account with "MCP" in the content
        - Include a section with "Query:" followed by your question
        - The script will detect this email, process it, and send a response
This implementation provides a basic MCP email agent that:
        - Authenticates with Gmail
        - Checks for unread emails
        - Identifies MCP-formatted emails
        - Extracts queries from those emails
        - Sends responses back to the sender
Runs continuously, checking for new emails every minute
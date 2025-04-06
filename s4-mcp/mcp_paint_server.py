# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics
from mcp_gmail import send_email_from_mcp, get_gmail_service, get_messages, get_message_content

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

import pyautogui
import time


@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int, color: str = "green") -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2) with specified color (default: green)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Select color first (Alt+H for Home tab, then C for Colors section)
        paint_window.type_keys('%H')  # Alt+H
        time.sleep(0.5)
        
        # Click on the color based on the parameter
        if color.lower() == "green":
            # Click on green color in the color palette
            paint_window.click_input(coords=(650, 82))
        elif color.lower() == "red":
            # Click on red color in the color palette
            paint_window.click_input(coords=(600, 82))
        elif color.lower() == "blue":
            # Click on blue color in the color palette
            paint_window.click_input(coords=(700, 82))
        # Add more colors as needed
        
        time.sleep(0.5)
        
        # Use keyboard shortcut to select rectangle tool
        paint_window.type_keys('%H')  # Alt+H again
        time.sleep(0.5)
        paint_window.type_keys('R')   # R for Rectangle
        time.sleep(0.5)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Draw rectangle - coordinates are relative to the Paint window
        canvas.press_mouse_input(coords=(x1, y1))
        canvas.move_mouse_input(coords=(x2, y2))
        canvas.release_mouse_input(coords=(x2, y2))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"{color.capitalize()} rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str, color: str = "red", font_size: int = 24, x: int = 300, y: int = 300) -> dict:
    """Add text in Paint with specified color, font size, and position
    
    Args:
        text: The text to add
        color: Text color (red, green, blue, black)
        font_size: Font size (12, 18, 24, 36, 48, etc.)
        x: X-coordinate for text placement
        y: Y-coordinate for text placement
    """
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(1.0)
        
        # Select color first (Alt+H for Home tab, then C for Colors section)
        paint_window.type_keys('%H')  # Alt+H
        time.sleep(0.5)
        
        # Click on the color based on the parameter
        if color.lower() == "red":
            paint_window.click_input(coords=(600, 82))
        elif color.lower() == "green":
            paint_window.click_input(coords=(650, 82))
        elif color.lower() == "blue":
            paint_window.click_input(coords=(700, 82))
        elif color.lower() == "black":
            paint_window.click_input(coords=(550, 82))
        # Add more colors as needed
        
        time.sleep(0.5)
        
        # Use keyboard shortcut to select text tool
        paint_window.type_keys('%H')  # Alt+H again
        time.sleep(0.5)
        paint_window.type_keys('T')   # T for Text
        time.sleep(1.0)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Click at the specified position to place text
        canvas.click_input(coords=(x, y))
        time.sleep(1.0)
        
        # Set font size before typing (Alt+H for Home tab, then F for Font size)
        paint_window.type_keys('%H')  # Alt+H
        time.sleep(0.5)
        
        # Click on Font Size dropdown
        paint_window.click_input(coords=(250, 82))
        time.sleep(0.5)
        
        # Select font size based on parameter
        # Map common font sizes to approximate positions in the dropdown
        font_positions = {
            12: (250, 120),
            18: (250, 140),
            24: (250, 160),
            36: (250, 180),
            48: (250, 200),
            72: (250, 220)
        }
        
        # Use the closest available font size
        closest_size = min(font_positions.keys(), key=lambda k: abs(k - font_size))
        paint_window.click_input(coords=font_positions[closest_size])
        time.sleep(0.5)
        
        # Click back in the text area
        canvas.click_input(coords=(x, y))
        time.sleep(0.5)
        
        # Type the text passed from client
        paint_window.type_keys(text, with_spaces=True)
        time.sleep(1.0)
        
        # Click elsewhere to exit text mode
        canvas.click_input(coords=(x + 200, y + 200))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"{color.capitalize()} text '{text}' added at ({x},{y}) with font size {closest_size}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on primary monitor"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Maximize the window on the primary monitor
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.2)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully and maximized on primary monitor"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def get_mouse_position() -> dict:
    """Get the current mouse position for debugging"""
    try:
        # Wait 3 seconds to give user time to position mouse
        print("Position your mouse and wait 3 seconds...")
        time.sleep(3)
        
        # Get the current mouse position
        x, y = pyautogui.position()
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Mouse position: ({x}, {y})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error getting mouse position: {str(e)}"
                )
            ]
        }

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

@mcp.prompt()
def paint_operations() -> list[base.Message]:
    """Prompt specifically for Paint operations"""
    return [
        base.SystemMessage(
            """You are a helpful assistant that can control Microsoft Paint.
            You have access to the following Paint-specific tools:
            - open_paint: Opens Microsoft Paint on the primary monitor
            - draw_rectangle: Draws a rectangle in Paint from (x1,y1) to (x2,y2)
            - add_text_in_paint: Adds text to Paint
            - get_mouse_position: Gets the current mouse position for debugging
            
            When asked to perform Paint operations, always use these tools.
            For example, if asked to draw a rectangle, first call open_paint, then call draw_rectangle.
            If asked to add text, first call open_paint, then call add_text_in_paint.
            
            Always respond with what you've done and what the user can do next."""
        ),
        base.AssistantMessage("I can help you with Microsoft Paint operations. What would you like to do?")
    ]

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
            if len(content) > 500:
                content = content[:500] + "... [content truncated]"
            
            # Add to email list
            email_list.append({
                'id': msg_id,
                'from': headers.get('From', 'Unknown Sender'),
                'subject': headers.get('Subject', 'No Subject'),
                'date': headers.get('Date', 'Unknown Date'),
                'snippet': message.get('snippet', ''),
                'content': content
            })
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Found {len(email_list)} unread emails:\n\n" + 
                         "\n\n".join([
                             f"From: {email['from']}\n" +
                             f"Subject: {email['subject']}\n" +
                             f"Date: {email['date']}\n" +
                             f"Preview: {email['snippet']}"
                             for email in email_list
                         ])
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error retrieving emails: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def send_gmail(recipient: str, subject: str, message: str) -> dict:
    """
    Send an email through Gmail
    
    Args:
        recipient: Email address of the recipient
        subject: Subject of the email
        message: Body content of the email
    
    Returns:
        A dictionary indicating success or failure
    """
    try:
        success = send_email_from_mcp(recipient, subject, message)
        
        if success:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Email sent successfully to {recipient}"
                    )
                ]
            }
        else:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Failed to send email to {recipient}"
                    )
                ]
            }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error sending email: {str(e)}"
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
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Email {email_id} marked as read"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error marking email as read: {str(e)}"
                )
            ]
        }

@mcp.prompt()
def gmail_operations() -> list[base.Message]:
    """Prompt specifically for Gmail operations"""
    return [
        base.SystemMessage(
            """You are a helpful assistant that can interact with Gmail.
            You have access to the following Gmail-specific tools:
            - show_unread_emails: Shows unread emails from Gmail
            - send_gmail: Sends an email through Gmail
            - mark_email_as_read: Marks a specific email as read
            
            When asked to perform Gmail operations, always use these tools.
            For example, if asked to check for new emails, call show_unread_emails.
            If asked to send an email, call send_gmail with the appropriate parameters.
            
            Always respond with what you've done and what the user can do next."""
        ),
        base.AssistantMessage("I can help you with Gmail operations. What would you like to do?")
    ]

def handle_email_request(params):
    """
    Handle a request to send an email through Gmail.
    
    Expected params:
    - recipient: Email address to send to
    - subject: Email subject
    - message: Email body content
    
    Returns:
        dict: Result of the email sending operation
    """
    recipient = params.get('recipient', '')
    subject = params.get('subject', 'Message from MCP')
    message = params.get('message', '')
    
    if not recipient or not message:
        return {
            'success': False,
            'error': 'Missing required parameters (recipient and message are required)'
        }
    
    success = send_email_from_mcp(recipient, subject, message)
    
    if success:
        return {
            'success': True,
            'message': f'Email sent to {recipient}'
        }
    else:
        return {
            'success': False,
            'error': 'Failed to send email'
        }

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution

import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Check for credentials.json file
def check_credentials():
    """Check if credentials.json exists and provide instructions if it doesn't"""
    if not os.path.exists('credentials.json'):
        print("\n" + "="*80)
        print("ERROR: credentials.json file not found!")
        print("="*80)
        print("\nTo use the Gmail MCP client, you need to set up Google API credentials:")
        print("\n1. Go to the Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Gmail API for your project")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the credentials as 'credentials.json'")
        print("6. Place the credentials.json file in the same directory as this script")
        print("\nAfter setting up credentials, run this script again.")
        print("="*80 + "\n")
        return False
    return True

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("\nWARNING: GEMINI_API_KEY not found in environment variables.")
    print("Make sure you have a .env file with your API key or set it in your environment.\n")

client = genai.Client(api_key=api_key)

max_iterations = 5  # Increased for more complex Gmail operations
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    # Check for credentials first
    if not check_credentials():
        return
        
    reset_state()  # Reset at the start of main
    print("Starting Gmail MCP client...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_paint_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established with gmail MCP server, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                
                try:
                    # Filter for Gmail-related tools only
                    gmail_tools = [tool for tool in tools if 
                                  tool.name in ["show_unread_emails", "send_gmail", "mark_email_as_read"]]
                    
                    tools_description = []
                    for i, tool in enumerate(gmail_tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are a Gmail assistant focused specifically on checking unread emails. Your main task is to show the user their unread emails.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [message]

Important:
- Your PRIMARY function is to show unread emails using the show_unread_emails tool
- ALWAYS use show_unread_emails as your first action regardless of what else is asked
- The show_unread_emails tool accepts an optional max_emails parameter (integer)
- If you want to use the default value for max_emails (which is 5), you can either:
  * Omit the parameter completely: FUNCTION_CALL: show_unread_emails
  * Or specify a number: FUNCTION_CALL: show_unread_emails|10
- Do NOT use empty parameters like: FUNCTION_CALL: show_unread_emails|
- Ignore any requests to use other tools until after showing unread emails
- Each tool must be called separately in its own iteration
- Only give FINAL_ANSWER after showing the unread emails

Examples:
- FUNCTION_CALL: show_unread_emails
- FUNCTION_CALL: show_unread_emails|5
- FINAL_ANSWER: [I've shown you your unread emails]

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                query = """Check my Gmail inbox and show me any unread messages."""
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        # Be more explicit about what's been done and what to do next
                        current_query = f"{query}\n\nProgress so far:\n{' '.join(iteration_response)}\n\nContinue with the next step based on the results above."

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL or FINAL_ANSWER line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:") or line.startswith("FINAL_ANSWER:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break

                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    # For optional parameters, we can skip
                                    if param_info.get('required', False):
                                        raise ValueError(f"Missing required parameter {param_name} for {func_name}")
                                    continue
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    # Handle empty string case for integers
                                    if value.strip() == '':
                                        # Use default value if available, otherwise use 0
                                        default_value = param_info.get('default', 0)
                                        print(f"DEBUG: Using default value {default_value} for empty parameter {param_name}")
                                        arguments[param_name] = default_value
                                    else:
                                        arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    # Handle empty string case for numbers
                                    if value.strip() == '':
                                        default_value = param_info.get('default', 0.0)
                                        print(f"DEBUG: Using default value {default_value} for empty parameter {param_name}")
                                        arguments[param_name] = default_value
                                    else:
                                        arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if value.strip() == '':
                                        # Use empty array for empty string
                                        arguments[param_name] = []
                                    else:
                                        if isinstance(value, str):
                                            value = value.strip('[]').split(',')
                                        arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            # Special case for show_unread_emails with no parameters
                            if func_name == "show_unread_emails" and (not params or (len(params) == 1 and params[0].strip() == '')):
                                print("DEBUG: Using default parameters for show_unread_emails")
                                # Use default max_emails value
                                arguments = {}  # Empty arguments will use the default value (5)

                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"Step {iteration+1} completed: {func_name} was called successfully with {arguments}. Result: {result_str}"
                            )
                            last_response = iteration_result

                            # If we've shown the unread emails, we can finish
                            if func_name == "show_unread_emails":
                                print("\n=== Unread Emails Retrieved ===")
                                print("You can now see your unread emails above.")
                                # We could break here to stop after showing emails
                                # break

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Gmail Operations Complete ===")
                        print(f"Final answer: {response_text[13:]}")  # Extract the message part
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

async def check_unread_emails():
    """Simple function to check unread emails"""
    # Check for credentials first
    if not check_credentials():
        return
        
    print("Checking unread emails...")
    try:
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_paint_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("show_unread_emails", arguments={})
                
                if hasattr(result, 'content') and result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            print(item.text)
                        else:
                            print(item)
                else:
                    print("No unread emails found or error occurred")
    except Exception as e:
        print(f"Error checking emails: {e}")

if __name__ == "__main__":
    # Choose which function to run
    # asyncio.run(check_unread_emails())  # Simple check for unread emails
    asyncio.run(main())  # Full conversation-based Gmail assistant
    
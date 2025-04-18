"""
Streamlit UI for the ChefChainAgent
"""
import streamlit as st
import json
import os
from typing import Dict, List, Any, Optional, Union
import time
import inspect
from openai import OpenAI
from openai.types.beta.threads import Run
from dotenv import load_dotenv, find_dotenv
import re
import sys
from datetime import datetime

# Add the current directory to the path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chef_agent import ChefChainAgent
from agent_tools import get_all_tools, TOOL_HANDLERS
import perception
import memory
import decision_making
import action

# Load environment variables from .env file
# Use find_dotenv to locate the .env file
load_dotenv(find_dotenv())

# Get the API key with a fallback error message
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found. Please add your API key to the .env file.")
    st.stop()

# Initialize OpenAI client with explicit API key
client = OpenAI(api_key=api_key)

# Initialize the ChefChainAgent with the same client
chef_agent = ChefChainAgent()

# Initialize the modules to ensure they're available
try:
    perception_module = perception.PerceptionModule(client)
    memory_module = memory.MemoryModule()
    decision_making_module = decision_making.DecisionMakingModule(client)
    action_module = action.ActionModule(client)
except Exception as e:
    st.warning(f"Error initializing cognitive modules: {str(e)}")
    st.info("This won't affect the chat functionality, but some module displays may be limited.")

# Create or get the assistant
def get_or_create_assistant():
    """Get or create the OpenAI Assistant"""
    # Check if we have a saved assistant ID
    if os.path.exists("assistant_id.txt"):
        with open("assistant_id.txt", "r") as f:
            assistant_id = f.read().strip()
            try:
                return client.beta.assistants.retrieve(assistant_id)
            except:
                pass  # If retrieval fails, create a new assistant
    
    # Create a new assistant with improved system prompt
    assistant = client.beta.assistants.create(
        name="Chef Chain Agent",
        instructions="""
        You are ChefChainAgent, a multi-tool LLM Agent that helps users create recipes and meal plans based on what's in their kitchen.
        
        # Reasoning Process
        Follow these steps when helping users, and explicitly state which step you're on:
        
        Step 1: Identify what can be cooked with current ingredients.
           - Analyze the available ingredients
           - Consider common recipe patterns
           - Tag this as "INGREDIENT ANALYSIS"
        
        Step 2: Adjust for health/taste preferences.
           - Consider dietary restrictions (vegan, gluten-free, etc.)
           - Adapt to health goals (low-calorie, high-protein, etc.)
           - Tag this as "PREFERENCE ADAPTATION"
        
        Step 3: Add missing ingredients if needed.
           - Identify essential ingredients that might be missing
           - Suggest common substitutions when possible
           - Tag this as "INGREDIENT COMPLETION"
        
        Step 4: Suggest alternate options or replacements.
           - Provide at least 2-3 recipe options when possible
           - Explain the trade-offs between options
           - Tag this as "OPTION GENERATION"
        
        Step 5: Generate meal plan (1-day or 7-day) if requested.
           - Balance nutritional content across meals
           - Consider ingredient reuse for efficiency
           - Tag this as "MEAL PLANNING"
        
        Step 6: Calculate estimated calories and shopping list.
           - Provide nutritional estimates
           - Organize shopping list by category
           - Tag this as "NUTRITION & SHOPPING"
        
        # Tool Usage Guidelines
        
        ## adjust_recipe Tool
        ONLY use the adjust_recipe tool when the user EXPLICITLY asks to:
        - Make a recipe healthier
        - Modify a specific recipe
        - Adjust a recipe for dietary restrictions
        - Update or change an existing recipe
        
        DO NOT use the adjust_recipe tool:
        - When first generating recipe options
        - When the user hasn't mentioned a specific recipe to modify
        - When the user is asking general questions about cooking
        - When the user is requesting a new recipe
        
        ## create_meal_plan Tool
        Only use this tool when the user explicitly asks for a meal plan.
        
        ## generate_shopping_list Tool
        Only use this tool when the user asks for a shopping list or when you've completed a recipe/meal plan.
        
        # Output Format
        Structure your responses in this format:
        1. Brief summary of what you understood from the user
        2. Your reasoning steps (tagged as described above)
        3. Final recommendations or recipe details
        4. Any follow-up questions to clarify user needs
        
        # Self-Verification
        Before providing final recommendations:
        - Verify that recipes match the user's dietary restrictions
        - Check that suggested recipes use the available ingredients
        - Ensure calorie estimates align with health goals
        - If any verification fails, explicitly note this and adjust your recommendation
        
        # Error Handling
        If you're uncertain about:
        - An ingredient: Ask for clarification
        - A cooking technique: Suggest an alternative approach
        - Nutritional information: Provide a range and note the uncertainty
        
        Think like a chef, a nutritionist, and a home cook — all in one!
        """,
        model="gpt-4o",
        tools=get_all_tools()
    )
    
    # Save the assistant ID
    with open("assistant_id.txt", "w") as f:
        f.write(assistant.id)
    
    return assistant

# Create or get a thread
def get_or_create_thread():
    """Get or create a thread for the conversation"""
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    return st.session_state.thread_id

# Add these functions that use the Memory module
def store_recipe_in_memory(recipe: Dict):
    """Store a recipe in the Memory module"""
    chef_agent.memory.store_recipe(recipe)

def store_recipes_in_memory(recipes: List[Dict]):
    """Store multiple recipes in the Memory module"""
    for recipe in recipes:
        if isinstance(recipe, dict) and "name" in recipe:
            store_recipe_in_memory(recipe)

def get_recipe_from_memory(recipe_name: Optional[str] = None) -> Optional[Dict]:
    """Get a recipe from the Memory module by name or the most recent one"""
    # Get past recipes from memory
    past_recipes = chef_agent.memory.get_past_recipes()
    
    if not past_recipes:
        return None
    
    if recipe_name:
        # Try to find an exact match
        for recipe in past_recipes:
            if recipe.get("name", "").lower() == recipe_name.lower():
                return recipe
        
        # Try to find a partial match
        for recipe in past_recipes:
            if recipe_name.lower() in recipe.get("name", "").lower():
                return recipe
    
    # If no name provided or no match found, return the most recent recipe
    return past_recipes[-1] if past_recipes else None

# Modify the handle_tool_execution function
def handle_tool_execution(tool_calls: List[Dict]) -> Dict[str, Any]:
    """Handle tool execution and return results"""
    import json  # Ensure json is imported here
    
    results = {}
    
    # Handle multi-tool use
    for tool_call in tool_calls:
        tool_call_id = tool_call.id
        function_name = tool_call.function.name
        
        # Handle multi-tool use case
        if function_name == "multi_tool_use.parallel":
            st.warning("Multi-tool use detected. Processing each tool individually.")
            try:
                function_args = json.loads(tool_call.function.arguments)
                tool_uses = function_args.get("tool_uses", [])
                
                # Process each tool use
                multi_results = {}
                for i, tool_use in enumerate(tool_uses):
                    recipient_name = tool_use.get("recipient_name", "")
                    if recipient_name.startswith("functions."):
                        # Extract the actual function name
                        actual_function = recipient_name.split("functions.")[1]
                        parameters = tool_use.get("parameters", {})
                        
                        st.markdown(f"**Processing sub-tool {i+1}:** `{actual_function}`")
                        
                        # Process this tool
                        if actual_function in TOOL_HANDLERS:
                            try:
                                # Special handling for adjust_recipe
                                if actual_function == "adjust_recipe" and "recipe" not in parameters:
                                    # Try to find a recipe
                                    recipe = extract_recipe_from_context()
                                    if recipe:
                                        parameters["recipe"] = recipe
                                        st.success(f"Using recipe: {recipe.get('name', 'Unknown')}")
                                    else:
                                        st.error("No recipe found to adjust")
                                        multi_results[f"tool_{i}"] = {
                                            "error": "Recipe not found",
                                            "message": "Please provide a recipe to adjust."
                                        }
                                        continue
                                
                                result = TOOL_HANDLERS[actual_function](parameters)
                                multi_results[f"tool_{i}"] = result
                                
                                # Store tool call in memory
                                chef_agent.memory.store_tool_call(
                                    actual_function, 
                                    parameters, 
                                    result
                                )
                            except Exception as e:
                                st.error(f"Error executing {actual_function}: {str(e)}")
                                multi_results[f"tool_{i}"] = {
                                    "error": str(e),
                                    "message": f"Error executing {actual_function}"
                                }
                        else:
                            multi_results[f"tool_{i}"] = {
                                "error": f"Unknown tool: {actual_function}"
                            }
                
                results[tool_call_id] = {
                    "output": json.dumps(multi_results)
                }
                continue
            except Exception as e:
                st.error(f"Error processing multi-tool use: {str(e)}")
                results[tool_call_id] = {
                    "output": json.dumps({"error": str(e)})
                }
                continue
        
        # Handle regular tool calls
        try:
            function_args = json.loads(tool_call.function.arguments)
            
            # Display the tool execution
            st.markdown(f"**Executing tool:** `{function_name}`")
            st.markdown("**Tool input:**")
            st.json(function_args)
            
            # Create a placeholder for cognitive layer output
            layer_output_placeholder = st.empty()
            
            if function_name in TOOL_HANDLERS:
                try:
                    # Special handling for adjust_recipe when recipe is missing
                    if function_name == "adjust_recipe" and "recipe" not in function_args:
                        st.warning("Recipe parameter is missing. Attempting to use the most recent recipe.")
                        
                        # Try to find a recipe
                        recipe = extract_recipe_from_context()
                        if recipe:
                            function_args["recipe"] = recipe
                            st.success(f"Using recipe: {recipe.get('name', 'Unknown')}")
                        else:
                            st.error("No recipe found to adjust")
                            results[tool_call_id] = {
                                "output": json.dumps({
                                    "error": "Recipe not found",
                                    "message": "Please provide a recipe to adjust."
                                })
                            }
                            continue
                    
                    # Display cognitive layers used
                    st.markdown("**Cognitive Layers Used**")
                    st.markdown("""
                    **Perception:** Understands preferences and adjustment requirements
                    
                    **Decision Making:** Adapts the recipe based on specified criteria
                    
                    **Memory:** Stores the adjusted recipe for future reference
                    """)
                    
                    # Execute with layer tracking
                    result = execute_with_layer_tracking(
                        function_name, 
                        function_args, 
                        layer_output_placeholder
                    )
                    
                    # Display the result
                    st.markdown("**Tool output:**")
                    st.json(result)
                    
                    # Store the result in the appropriate format
                    results[tool_call_id] = {
                        "output": json.dumps(result)
                    }
                except Exception as e:
                    st.error(f"Error executing {function_name}: {str(e)}")
                    results[tool_call_id] = {
                        "output": json.dumps({
                            "error": str(e),
                            "message": f"Failed to execute {function_name}. Please try again with different parameters.",
                            "timestamp": datetime.now().isoformat()
                        })
                    }
            else:
                st.error(f"Unknown tool: {function_name}")
                results[tool_call_id] = {
                    "output": json.dumps({
                        "error": f"Unknown tool: {function_name}"
                    })
                }
        except Exception as e:
            st.error(f"Error parsing tool arguments: {str(e)}")
            results[tool_call_id] = {
                "output": json.dumps({
                    "error": str(e),
                    "message": "Failed to parse tool arguments."
                })
            }
    
    return results

# Modify the extract_recipe_from_context function
def extract_recipe_from_context() -> Optional[Dict]:
    """Extract recipe from conversation context"""
    import json  # Ensure json is imported here
    
    try:
        # Get past recipes from memory
        past_recipes = chef_agent.memory.get_past_recipes()
        if not past_recipes:
            st.warning("No recipes found in memory")
            return create_default_recipe()
        
        # Try to get recent messages
        thread_id = get_or_create_thread()
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        
        # Look for recipe names in recent messages
        recipe_name = None
        
        # First, check if there's a recipe mentioned in recent messages
        for message in messages.data:
            if message.role == "user":
                content = ""
                for content_block in message.content:
                    if content_block.type == "text":
                        content += content_block.text.value
                
                # Look for recipe names in the message
                for recipe in past_recipes:
                    recipe_name_from_memory = recipe.get("name", "")
                    if recipe_name_from_memory and recipe_name_from_memory.lower() in content.lower():
                        recipe_name = recipe_name_from_memory
                        st.info(f"Found recipe name in message: {recipe_name}")
                        break
                
                # If no direct match, look for phrases like "make X healthier"
                if not recipe_name:
                    patterns = [
                        r"make\s+(.+?)\s+healthier",
                        r"adjust\s+(.+?)\s+to",
                        r"modify\s+(.+?)\s+recipe",
                        r"update\s+(.+?)\s+recipe",
                        r"change\s+(.+?)\s+to",
                        r"improve\s+(.+?)\s+recipe"
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content.lower())
                        if matches:
                            potential_name = matches[0].strip()
                            # Check if this matches any known recipe
                            for recipe in past_recipes:
                                recipe_name_from_memory = recipe.get("name", "")
                                if (recipe_name_from_memory and 
                                    (potential_name in recipe_name_from_memory.lower() or 
                                     recipe_name_from_memory.lower() in potential_name)):
                                    recipe_name = recipe_name_from_memory
                                    st.info(f"Found recipe name from pattern: {recipe_name}")
                                    break
        
        # Also check session state messages for recipe mentions
        if "messages" in st.session_state and not recipe_name:
            recent_messages = st.session_state.messages[-5:] if len(st.session_state.messages) > 5 else st.session_state.messages
            
            for message in recent_messages:
                if message["role"] == "user":
                    content = message["content"].lower()
                    
                    # Look for recipe names in the message
                    for recipe in past_recipes:
                        recipe_name_from_memory = recipe.get("name", "")
                        if recipe_name_from_memory and recipe_name_from_memory.lower() in content:
                            recipe_name = recipe_name_from_memory
                            st.info(f"Found recipe name in session history: {recipe_name}")
                            break
                    
                    # Look for modification patterns
                    if not recipe_name:
                        patterns = [
                            r"make\s+(.+?)\s+healthier",
                            r"adjust\s+(.+?)\s+to",
                            r"modify\s+(.+?)\s+recipe",
                            r"update\s+(.+?)\s+recipe",
                            r"change\s+(.+?)\s+to",
                            r"improve\s+(.+?)\s+recipe"
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                potential_name = matches[0].strip()
                                # Check if this matches any known recipe
                                for recipe in past_recipes:
                                    recipe_name_from_memory = recipe.get("name", "")
                                    if (recipe_name_from_memory and 
                                        (potential_name in recipe_name_from_memory.lower() or 
                                         recipe_name_from_memory.lower() in potential_name)):
                                        recipe_name = recipe_name_from_memory
                                        st.info(f"Found recipe name from session pattern: {recipe_name}")
                                        break
        
        # If no recipe name found in messages, check recent tool calls
        if not recipe_name:
            tool_calls = chef_agent.memory.get_recent_tool_calls(5)
            for tool_call in tool_calls:
                if tool_call.get("tool_name") == "generate_recipe_options":
                    output = tool_call.get("output", {})
                    if isinstance(output, dict) and "recipes" in output:
                        recipes = output["recipes"]
                        if recipes and len(recipes) > 0:
                            recipe_name = recipes[0].get("name", "")
                            st.info(f"Found recipe name from recent tool call: {recipe_name}")
                            break
                elif tool_call.get("tool_name") == "adjust_recipe":
                    output = tool_call.get("output", {})
                    if isinstance(output, dict) and "name" in output:
                        recipe_name = output["name"]
                        st.info(f"Found recipe name from recent adjustment: {recipe_name}")
                        break
        
        # If no recipe name found in messages, use the most recent recipe
        if not recipe_name and past_recipes:
            most_recent = past_recipes[-1]
            recipe_name = most_recent.get("name", "")
            st.info(f"Using most recent recipe: {recipe_name}")
        
        # Get the recipe by name
        for recipe in past_recipes:
            if recipe.get("name", "") == recipe_name:
                return recipe
        
        # If still not found, return the most recent recipe
        if past_recipes:
            st.info(f"Using recipe: {past_recipes[-1].get('name', 'Unknown')}")
            return past_recipes[-1]
        
        # If no recipes found, create a default recipe
        return create_default_recipe()
    except Exception as e:
        st.error(f"Error extracting recipe from context: {str(e)}")
        return create_default_recipe()

# Helper function to create a default recipe
def create_default_recipe() -> Dict:
    """Create a default recipe when none is found"""
    st.warning("Creating a default recipe since none was found")
    return {
        "name": "Basic Tomato Soup",
        "ingredients": [
            {"name": "tomatoes", "quantity": 4, "unit": "large"},
            {"name": "onion", "quantity": 1, "unit": "medium"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "vegetable broth", "quantity": 2, "unit": "cups"},
            {"name": "olive oil", "quantity": 2, "unit": "tablespoons"},
            {"name": "salt", "quantity": 1, "unit": "teaspoon"},
            {"name": "pepper", "quantity": 0.5, "unit": "teaspoon"}
        ],
        "instructions": [
            "Dice the tomatoes, onion, and garlic.",
            "Heat olive oil in a pot over medium heat.",
            "Add onion and garlic, sauté until translucent.",
            "Add tomatoes and cook for 5 minutes.",
            "Pour in vegetable broth and bring to a simmer.",
            "Season with salt and pepper.",
            "Simmer for 15 minutes.",
            "Blend until smooth if desired."
        ],
        "time": {"prep": 10, "cook": 20, "total": 30},
        "servings": 4,
        "calories_per_serving": 120,
        "tags": ["soup", "vegetarian", "easy"],
        "description": "A simple and delicious tomato soup that's perfect for any occasion."
    }

# Helper function to determine which cognitive layers are used by a tool
def get_cognitive_layers_for_tool(function_name: str) -> Dict[str, str]:
    """Get the cognitive layers used by a specific tool"""
    layers = {}
    
    if function_name == "generate_recipe_options":
        layers["Perception"] = "Parses ingredients and preferences from text"
        layers["Decision Making"] = "Generates recipe options based on ingredients and preferences"
        layers["Memory"] = "Stores ingredients and preferences for future reference"
    
    elif function_name == "create_detailed_recipe":
        layers["Action"] = "Generates detailed recipe with instructions"
        layers["Memory"] = "Stores the recipe for future reference"
    
    elif function_name == "create_meal_plan":
        layers["Perception"] = "Parses ingredients and preferences from text"
        layers["Decision Making"] = "Creates a meal plan based on ingredients and preferences"
        layers["Action"] = "Generates a shopping list for missing ingredients"
        layers["Memory"] = "Stores the meal plan for future reference"
    
    elif function_name == "adjust_recipe":
        layers["Perception"] = "Understands preferences and adjustment requirements"
        layers["Decision Making"] = "Adapts the recipe based on specified criteria"
        layers["Memory"] = "Stores the adjusted recipe for future reference"
    
    return layers

# Update the execute_with_layer_tracking function
def execute_with_layer_tracking(function_name: str, function_args: Dict, output_placeholder) -> Dict:
    """Execute a tool and track cognitive layer activity"""
    # Import necessary modules at the function level to ensure they're available
    import json
    from datetime import datetime
    
    # Get the original handler
    handler = TOOL_HANDLERS[function_name]
    
    # Create a container for layer outputs
    layer_outputs = {}
    
    # Update the layer output placeholder
    def update_layer_output(outputs, placeholder):
        output_text = "\n".join([f"**{key}**: {value}" for key, value in outputs.items()])
        placeholder.markdown(output_text)
    
    try:
        # Special handling for adjust_recipe when recipe is missing or invalid
        if function_name == "adjust_recipe":
            if "recipe" not in function_args or not function_args["recipe"]:
                st.warning("Recipe parameter is missing or invalid. Attempting to use the most recent recipe.")
                recipe = extract_recipe_from_context()
                if recipe:
                    function_args["recipe"] = recipe
                    st.success(f"Using recipe: {recipe.get('name', 'Unknown')}")
                else:
                    st.error("No recipe found to adjust")
                    return {
                        "error": "Recipe not found",
                        "message": "Please provide a recipe to adjust.",
                        "timestamp": datetime.now().isoformat()
                    }
        
        # Execute the handler with appropriate error handling
        result = handler(function_args)
        
        # Store the tool call in memory with timestamp
        try:
            # Add timestamp to the result if it's a dictionary
            if isinstance(result, dict) and "timestamp" not in result:
                result["timestamp"] = datetime.now().isoformat()
            
            chef_agent.memory.store_tool_call(function_name, function_args, result)
        except Exception as e:
            st.warning(f"Failed to store tool call in memory: {str(e)}")
        
        # Special handling for specific tools
        if function_name == "generate_recipe_options" and isinstance(result, dict) and "recipes" in result:
            try:
                # Store each recipe in memory
                for recipe in result["recipes"]:
                    chef_agent.memory.store_recipe(recipe)
                st.success(f"Stored {len(result['recipes'])} recipes in memory")
            except Exception as e:
                st.warning(f"Failed to store recipes in memory: {str(e)}")
        
        # Store adjusted recipe
        if function_name == "adjust_recipe" and isinstance(result, dict) and "name" in result:
            try:
                chef_agent.memory.store_recipe(result)
                st.success(f"Stored adjusted recipe '{result['name']}' in memory")
            except Exception as e:
                st.warning(f"Failed to store adjusted recipe in memory: {str(e)}")
        
        # Store meal plan
        if function_name == "create_meal_plan" and isinstance(result, dict):
            try:
                chef_agent.memory.store_meal_plan(result)
                st.success(f"Stored meal plan in memory")
            except Exception as e:
                st.warning(f"Failed to store meal plan in memory: {str(e)}")
        
        return result
    except Exception as e:
        st.error(f"Error executing {function_name}: {str(e)}")
        # Return a structured error response with timestamp
        error_response = {
            "error": str(e),
            "message": f"Failed to execute {function_name}. Please try again with different parameters.",
            "timestamp": datetime.now().isoformat()
        }
        return error_response

# Process the user message
def process_message(user_message: str):
    """Process the user message and get a response"""
    thread_id = get_or_create_thread()
    
    # Add the user message to the thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )
    
    # Store the user message in perception layer
    try:
        # Parse ingredients if present
        ingredients = perception_module.parse_ingredients(user_message)
        if ingredients:
            chef_agent.memory.store_perception({
                "type": "ingredients",
                "input": user_message,
                "output": ingredients
            })
            
            # Also store ingredients in memory
            chef_agent.memory.store_ingredients(ingredients)
        
        # Parse preferences if present
        preferences = perception_module.understand_preferences(user_message)
        if preferences:
            chef_agent.memory.store_perception({
                "type": "preferences",
                "input": user_message,
                "output": preferences
            })
            
            # Also store preferences in memory
            chef_agent.memory.store_user_preferences(preferences)
    except Exception as e:
        st.warning(f"Error processing perception layer: {str(e)}")
    
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=get_or_create_assistant().id
    )
    
    # Poll for the run to complete
    while run.status in ["queued", "in_progress"]:
        st.markdown(f"*Status: {run.status}*")
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        
        # Handle tool calls
        if run.status == "requires_action" and run.required_action:
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            
            # Log the tool calls for debugging
            st.info(f"Processing {len(tool_calls)} tool calls")
            
            try:
                tool_outputs = handle_tool_execution(tool_calls)
                
                # Submit tool outputs
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=[
                        {
                            "tool_call_id": tool_call_id,
                            "output": output["output"]
                        }
                        for tool_call_id, output in tool_outputs.items()
                    ]
                )
            except Exception as e:
                st.error(f"Error handling tool execution: {str(e)}")
                # Create a fallback response
                fallback_response = {
                    "error": "Tool execution failed",
                    "message": f"There was an error processing your request: {str(e)}. Please try again with different ingredients or instructions."
                }
                
                # Submit fallback outputs for all tool calls
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=[
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(fallback_response)
                        }
                        for tool_call in tool_calls
                    ]
                )
    
    # Get the messages
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    
    # Get the latest assistant message
    assistant_response = None
    for message in messages.data:
        if message.role == "assistant":
            assistant_response = message.content
            break
    
    # Store the interaction in memory with more details
    if assistant_response:
        assistant_text = "\n".join([
            content_block.text.value 
            for content_block in assistant_response 
            if content_block.type == "text"
        ])
        
        # Store the basic interaction
        chef_agent.memory.store_interaction(user_message, assistant_text)
        
        # Store the full conversation context
        store_conversation_context(user_message, assistant_text, thread_id)
    
    return assistant_response

# Display cognitive layer modules
def display_cognitive_layers():
    """Display the cognitive layer modules"""
    # Import modules inside the function to ensure they're available in all scopes
    import inspect
    import sys
    import os
    
    # Ensure these modules are imported at the function level
    # so they're available in exception handlers
    import perception as perception_module
    import memory as memory_module
    import decision_making as decision_module
    import action as action_module
    
    st.header("Cognitive Layer Modules")
    
    # Create tabs for each module
    tabs = st.tabs(["Perception", "Memory", "Decision Making", "Action", "Memory Contents"])
    
    # Perception Module
    with tabs[0]:
        st.subheader("Perception Module")
        st.markdown("Handles understanding user input and context")
        
        try:
            # Show the module description
            st.markdown("""
            The Perception module is responsible for:
            - Parsing ingredients from user input
            - Understanding user preferences and dietary restrictions
            - Converting unstructured text into structured data
            """)
            
            # Try to display module code
            try:
                st.code(inspect.getsource(perception_module.PerceptionModule), language="python")
            except Exception as e:
                st.warning(f"Could not display module source code: {str(e)}")
                
                # Alternative: Display a description of the methods
                st.markdown("""
                ### Key Methods:
                
                **parse_ingredients(ingredients_text)**
                - Parses a text description of ingredients into structured data
                - Returns a list of Ingredient objects with name, quantity, and unit
                
                **understand_preferences(preferences_text)**
                - Extracts dietary preferences and restrictions from text
                - Returns a UserPreferences object with dietary needs and health goals
                """)
            
            # Show recent perceptions
            st.subheader("Recent Perceptions")
            try:
                perceptions = chef_agent.memory.get_recent_perceptions(5)
                if perceptions:
                    for i, perception in enumerate(perceptions):
                        with st.expander(f"{i+1}. {perception.get('type', 'Unknown Perception')} - {perception.get('timestamp', '')}"):
                            st.markdown("**Input:**")
                            st.write(perception.get("input", ""))
                            st.markdown("**Output:**")
                            st.json(perception.get("output", {}))
                else:
                    st.info("No perceptions stored yet.")
            except Exception as e:
                st.warning(f"Could not display recent perceptions: {str(e)}")
        except Exception as e:
            st.error(f"Error displaying Perception Module: {str(e)}")
            
            # Fallback description
            st.markdown("""
            ### Perception Module (Description)
            
            The Perception module is responsible for understanding user input and converting it to structured data.
            It includes methods for parsing ingredients and understanding user preferences.
            
            Unfortunately, the module source code cannot be displayed due to an error.
            """)
    
    # Memory Module
    with tabs[1]:
        st.subheader("Memory Module")
        st.markdown("Handles storage and retrieval of information")
        
        try:
            # Show the module description
            st.markdown("""
            The Memory module is responsible for:
            - Storing recipes, ingredients, and user preferences
            - Retrieving past information when needed
            - Maintaining persistent storage across sessions
            """)
            
            # Try to display module code
            try:
                st.code(inspect.getsource(memory_module.MemoryModule), language="python")
            except Exception as e:
                st.warning(f"Could not display module source code: {str(e)}")
                
                # Alternative: Display a description of the methods
                st.markdown("""
                ### Key Methods:
                
                **store_recipe(recipe)**
                - Stores a recipe in memory
                - Updates existing recipes with the same name
                
                **get_past_recipes()**
                - Retrieves all stored recipes
                
                **store_user_preferences(preferences)**
                - Stores user dietary preferences and restrictions
                """)
            
            # Show stored recipes
            st.subheader("Stored Recipes")
            try:
                recipes = chef_agent.memory.get_past_recipes()
                if recipes:
                    for i, recipe in enumerate(recipes):
                        with st.expander(f"{i+1}. {recipe.get('name', 'Unnamed Recipe')}"):
                            st.json(recipe)
                else:
                    st.info("No recipes stored yet.")
            except Exception as e:
                st.warning(f"Could not display stored recipes: {str(e)}")
            
            # Show user preferences
            st.subheader("User Preferences")
            try:
                preferences = chef_agent.memory.get_user_preferences()
                if preferences:
                    st.json(preferences)
                else:
                    st.info("No user preferences stored yet.")
            except Exception as e:
                st.warning(f"Could not display user preferences: {str(e)}")
            
            # Show available ingredients
            st.subheader("Available Ingredients")
            try:
                ingredients = chef_agent.memory.get_available_ingredients()
                if ingredients:
                    st.json(ingredients)
                else:
                    st.info("No ingredients stored yet.")
            except Exception as e:
                st.warning(f"Could not display available ingredients: {str(e)}")
        except Exception as e:
            st.error(f"Error displaying Memory Module: {str(e)}")
            
            # Fallback description
            st.markdown("""
            ### Memory Module (Description)
            
            The Memory module handles storage and retrieval of information such as recipes,
            user preferences, and available ingredients. It provides persistent storage
            across sessions.
            
            Unfortunately, the module source code cannot be displayed due to an error.
            """)
    
    # Decision Making Module
    with tabs[2]:
        st.subheader("Decision Making Module")
        st.markdown("Handles reasoning and planning")
        
        try:
            # Show the module description
            st.markdown("""
            The Decision Making module is responsible for:
            - Generating recipe options based on available ingredients
            - Creating meal plans that balance nutrition and preferences
            - Adjusting recipes to meet dietary requirements
            """)
            
            # Try to display module code
            try:
                st.code(inspect.getsource(decision_module.DecisionMakingModule), language="python")
            except Exception as e:
                st.warning(f"Could not display module source code: {str(e)}")
                
                # Alternative: Display a description of the methods
                st.markdown("""
                ### Key Methods:
                
                **generate_recipe_options(ingredients, preferences, num_options)**
                - Generates multiple recipe options based on available ingredients
                - Considers user preferences and dietary restrictions
                
                **create_meal_plan(ingredients, preferences, days)**
                - Creates a meal plan for a specified number of days
                - Balances nutrition and ingredient usage across meals
                """)
            
            # Show recent decisions
            st.subheader("Recent Decisions")
            try:
                decisions = chef_agent.memory.get_recent_decisions(5)
                if decisions:
                    for i, decision in enumerate(decisions):
                        with st.expander(f"{i+1}. {decision.get('type', 'Unknown Decision')} - {decision.get('timestamp', '')}"):
                            st.markdown("**Input:**")
                            st.json(decision.get("input", {}))
                            st.markdown("**Output:**")
                            st.json(decision.get("output", {}))
                else:
                    st.info("No decisions stored yet.")
            except Exception as e:
                st.warning(f"Could not display recent decisions: {str(e)}")
        except Exception as e:
            st.error(f"Error displaying Decision Making Module: {str(e)}")
            
            # Fallback description
            st.markdown("""
            ### Decision Making Module (Description)
            
            The Decision Making module handles reasoning and planning for recipes and meal plans.
            It generates recipe options and creates balanced meal plans based on available ingredients.
            
            Unfortunately, the module source code cannot be displayed due to an error.
            """)
    
    # Action Module
    with tabs[3]:
        st.subheader("Action Module")
        st.markdown("Handles executing actions and generating outputs")
        
        try:
            # Show the module description
            st.markdown("""
            The Action module is responsible for:
            - Generating detailed recipes with instructions
            - Creating shopping lists for missing ingredients
            - Calculating nutritional information for recipes
            """)
            
            # Try to display module code
            try:
                st.code(inspect.getsource(action_module.ActionModule), language="python")
            except Exception as e:
                st.warning(f"Could not display module source code: {str(e)}")
                
                # Alternative: Display a description of the methods
                st.markdown("""
                ### Key Methods:
                
                **generate_detailed_recipe(recipe_option)**
                - Expands a recipe option into a detailed recipe with instructions
                - Adds cooking times, difficulty level, and serving information
                
                **generate_shopping_list(recipes, available_ingredients)**
                - Creates a shopping list for missing ingredients
                - Organizes ingredients by category for easier shopping
                """)
            
            # Show recent actions
            st.subheader("Recent Actions")
            try:
                actions = chef_agent.memory.get_recent_actions(5)
                if actions:
                    for i, action in enumerate(actions):
                        with st.expander(f"{i+1}. {action.get('type', 'Unknown Action')} - {action.get('timestamp', '')}"):
                            st.markdown("**Input:**")
                            st.json(action.get("input", {}))
                            st.markdown("**Output:**")
                            st.json(action.get("output", {}))
                else:
                    st.info("No actions stored yet.")
            except Exception as e:
                st.warning(f"Could not display recent actions: {str(e)}")
        except Exception as e:
            st.error(f"Error displaying Action Module: {str(e)}")
            
            # Fallback description
            st.markdown("""
            ### Action Module (Description)
            
            The Action module handles executing specific tasks like generating detailed recipes
            and creating shopping lists. It transforms high-level recipe concepts into
            actionable instructions.
            
            Unfortunately, the module source code cannot be displayed due to an error.
            """)
    
    # Memory Contents
    with tabs[4]:
        st.subheader("Memory Contents")
        st.markdown("Complete history of interactions and tool calls")
        
        try:
            # Create subtabs for different memory types
            memory_tabs = st.tabs(["Interactions", "Tool Calls", "Recipes", "Meal Plans", "Memory File"])
            
            # Interactions
            with memory_tabs[0]:
                st.subheader("User-Assistant Interactions")
                interactions = chef_agent.memory.get_recent_interactions(10)
                if interactions:
                    for i, interaction in enumerate(interactions):
                        with st.expander(f"Interaction {i+1} - {interaction.get('timestamp', '')}"):
                            st.markdown("**User:**")
                            st.markdown(interaction.get("user_message", ""))
                            st.markdown("**Assistant:**")
                            st.markdown(interaction.get("assistant_response", ""))
                else:
                    st.info("No interactions stored yet.")
            
            # Tool Calls
            with memory_tabs[1]:
                st.subheader("Tool Calls")
                tool_calls = chef_agent.memory.get_recent_tool_calls(10)
                if tool_calls:
                    for i, tool_call in enumerate(tool_calls):
                        with st.expander(f"{i+1}. {tool_call.get('tool_name', 'Unknown Tool')} - {tool_call.get('timestamp', '')}"):
                            st.markdown("**Input:**")
                            st.json(tool_call.get("input", {}))
                            st.markdown("**Output:**")
                            st.json(tool_call.get("output", {}))
                else:
                    st.info("No tool calls stored yet.")
            
            # Recipes
            with memory_tabs[2]:
                st.subheader("Stored Recipes")
                recipes = chef_agent.memory.get_past_recipes()
                if recipes:
                    for i, recipe in enumerate(recipes):
                        with st.expander(f"{i+1}. {recipe.get('name', 'Unnamed Recipe')} - {recipe.get('timestamp', '')}"):
                            st.json(recipe)
                else:
                    st.info("No recipes stored yet.")
            
            # Meal Plans
            with memory_tabs[3]:
                st.subheader("Meal Plans")
                try:
                    meal_plans = chef_agent.memory.get_recent_meal_plans(10)
                    if meal_plans:
                        for i, plan in enumerate(meal_plans):
                            with st.expander(f"Meal Plan {i+1} - {plan.get('timestamp', '')}"):
                                st.json(plan)
                    else:
                        st.info("No meal plans stored yet.")
                except Exception as e:
                    st.warning(f"Could not display meal plans: {str(e)}")
            
            # Memory File
            with memory_tabs[4]:
                st.subheader("Memory File Contents")
                if os.path.exists(chef_agent.memory.memory_file):
                    try:
                        with open(chef_agent.memory.memory_file, "r") as f:
                            memory_content = json.load(f)
                        st.json(memory_content)
                    except Exception as e:
                        st.error(f"Error loading memory file: {str(e)}")
                else:
                    st.info("Memory file does not exist yet.")
        except Exception as e:
            st.error(f"Error displaying Memory Contents: {str(e)}")

# Add a debug function to check memory status
def debug_memory():
    """Debug the memory module"""
    st.subheader("Memory Debug Information")
    
    # Check if memory file exists
    memory_file = chef_agent.memory.memory_file
    st.write(f"Memory file path: {memory_file}")
    st.write(f"Memory file exists: {os.path.exists(memory_file)}")
    
    # Try to load memory content
    try:
        with open(memory_file, "r") as f:
            memory_content = json.load(f)
        st.write(f"Memory file size: {len(json.dumps(memory_content))} bytes")
        st.write(f"Memory sections: {list(memory_content.keys())}")
        
        # Count items in each section
        for key, value in memory_content.items():
            if isinstance(value, list):
                st.write(f"  - {key}: {len(value)} items")
            elif isinstance(value, dict):
                st.write(f"  - {key}: {len(value)} keys")
            else:
                st.write(f"  - {key}: {type(value)}")
    except Exception as e:
        st.error(f"Error loading memory file: {str(e)}")
    
    # Check memory module methods
    st.write("Memory module methods:")
    for method_name in dir(chef_agent.memory):
        if not method_name.startswith("_") and callable(getattr(chef_agent.memory, method_name)):
            st.write(f"  - {method_name}")

# Streamlit UI
def main():
    st.title("🧑‍🍳 Chef Chain Agent")
    
    # Create a sidebar for navigation
    page = st.sidebar.radio("Navigation", ["Chat", "Cognitive Layers", "About"])
    
    if page == "Chat":
        st.markdown("""
        Welcome to Chef Chain Agent! I can help you create recipes and meal plans based on what's in your kitchen.
        
        Just tell me:
        1. What ingredients you have
        2. Your dietary preferences or restrictions
        3. What you'd like to make
        """)
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Get user input
        if prompt := st.chat_input("What ingredients do you have?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process the message
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = process_message(prompt)
                    for content_block in response:
                        if content_block.type == "text":
                            st.markdown(content_block.text.value)
            
            # Add assistant response to chat history
            assistant_response = "\n".join([
                content_block.text.value 
                for content_block in response 
                if content_block.type == "text"
            ])
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    elif page == "Cognitive Layers":
        display_cognitive_layers()
    
    elif page == "About":
        st.header("About Chef Chain Agent")
        st.markdown("""
        ## Multi-tool LLM Chef Agent
        
        This application uses a multi-tool LLM Agent that creates recipes based on what's in your kitchen, 
        adjusts them for health goals or taste preferences, and then recommends meal plans.
        
        ### Agent Structure
        The agent is structured with 4 cognitive layers:
        
        1. **Perception**: Understands user input and extracts structured data
        2. **Memory**: Stores and retrieves information about recipes, preferences, and ingredients
        3. **Decision-Making**: Generates recipe options and meal plans based on available data
        4. **Action**: Executes specific tasks like generating detailed recipes and shopping lists
        
        ### Technologies Used
        - OpenAI API for language model capabilities
        - Streamlit for the user interface
        - Instructor for enhanced OpenAI client functionality
        - Pydantic for data validation and settings management
        """)
        
        # Display environment info
        st.subheader("Environment")
        st.markdown(f"**OpenAI API Key**: {'Configured ✅' if api_key else 'Missing ❌'}")
        
        # Display .env file content (without showing the actual API key)
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_content = f.read()
            
            # Replace the actual API key with asterisks
            if "OPENAI_API_KEY" in env_content:
                env_lines = env_content.split("\n")
                for i, line in enumerate(env_lines):
                    if line.startswith("OPENAI_API_KEY="):
                        key_part = line.split("=")[1]
                        if len(key_part) > 8:
                            masked_key = key_part[:4] + "*" * (len(key_part) - 8) + key_part[-4:]
                            env_lines[i] = f"OPENAI_API_KEY={masked_key}"
                
                env_content = "\n".join(env_lines)
            
            st.code(env_content, language="text")
        
        # Add memory debugging
        if st.button("Debug Memory"):
            debug_memory()

def store_conversation_context(user_message: str, assistant_response: str, thread_id: str):
    """Store the full conversation context including thread history"""
    try:
        # Get the full thread history
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        
        # Extract the conversation history
        conversation_history = []
        for message in reversed(messages.data):
            role = message.role
            content = "\n".join([
                content_block.text.value 
                for content_block in message.content 
                if content_block.type == "text"
            ])
            
            conversation_history.append({
                "role": role,
                "content": content,
                "created_at": message.created_at
            })
        
        # Get recent tool calls
        tool_calls = chef_agent.memory.get_recent_tool_calls(5)
        
        # Store the enhanced interaction
        enhanced_interaction = {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "conversation_history": conversation_history,
            "recent_tool_calls": tool_calls,
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory
        chef_agent.memory.store_enhanced_interaction(enhanced_interaction)
        
    except Exception as e:
        st.warning(f"Error storing conversation context: {str(e)}")

if __name__ == "__main__":
    main() 
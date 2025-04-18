# Chef Chain Agent

A multi-tool LLM Agent that creates recipes based on what's in your kitchen, adjusts them for health goals or taste preferences, and then recommends meal plans.

## Overview
Chef Chain Agent is an intelligent cooking assistant powered by OpenAI's GPT-4o model. It uses a cognitive architecture with four distinct layers to understand user requests, generate appropriate recipes, and create meal plans based on available ingredients and dietary preferences.

### Chef Chain Agent Architecture

#### Cognitive Architecture
The agent is structured with 4 cognitive layers:
1. Perception: Understands user input and extracts structured data
2. Memory: Stores and retrieves information about recipes, preferences, and ingredients
3. Decision-Making: Generates recipe options and meal plans based on available data
4. Action: Executes specific tasks like generating detailed recipes and shopping lists

#### Perception Module
1. The Perception module is responsible for understanding user input and converting it to structured data:
2. parse_ingredients(): Extracts ingredient information from text, including name, quantity, and unit
3. understand_preferences(): Identifies dietary preferences, restrictions, allergies, and health goals

#### Memory Module
1. The Memory module handles storage and retrieval of information:
2. store_recipe(): Saves recipes with timestamps and updates existing ones
3. get_past_recipes(): Retrieves all stored recipes
4. store_user_preferences(): Saves dietary preferences and restrictions
5. store_ingredients(): Records available ingredients
6. store_enhanced_interaction(): Saves complete conversation context for better continuity
7. get_conversation_by_thread_id(): Retrieves all interactions for a specific conversation thread

#### Decision Making Module
1. The Decision Making module handles reasoning and planning:
2. generate_recipe_options(): Creates multiple recipe options based on available ingredients
3. create_meal_plan(): Designs balanced meal plans for specified number of days
4. adjust_recipe(): Modifies recipes to meet specific criteria (healthier, vegetarian, etc.)

#### Action Module
1. The Action module executes specific tasks:
2. generate_detailed_recipe(): Expands recipe options into detailed instructions
3. generate_shopping_list(): Creates lists of missing ingredients
4. format_recipe_output(): Formats recipes for display
5. format_meal_plan_output(): Formats meal plans for display

#### System Prompt
The agent uses a carefully crafted system prompt that guides its behavior:
'''
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

'''

#### Tools
The agent has access to four main tools:
1. generate_recipe_options: Creates recipe suggestions based on ingredients and preferences
2. create_detailed_recipe: Expands a recipe option into detailed instructions
3. create_meal_plan: Designs meal plans for multiple days
4. adjust_recipe: Modifies recipes to meet specific criteria

#### Tool Execution
The tool execution process:
1. The agent identifies which tool to use based on user request
2. The appropriate cognitive layers are activated
3. Results are stored in memory for future reference
4. Formatted output is presented to the user

#### Frontend Components
The Streamlit-based UI has three main pages:
1. Chat Interface
2. Input field for user messages
3. Chat history display
4. Status indicators for tool execution

#### Cognitive Layers
Displays the inner workings of the agent:
1. Source code for each module
2. Recent perceptions, decisions, and actions
3. Memory contents including stored recipes and preferences

#### About Page
Overview of the agent architecture
Environment information
Memory debugging tools

#### Getting Started
Clone this repository
Install dependencies: pip install -r requirements.txt
Create a .env file with your OpenAI API key (see .env.example)
Run the application: streamlit run app.py

#### Technologies Used
1. OpenAI API for language model capabilities
2. Streamlit for the user interface
3. Instructor for enhanced OpenAI client functionality
4. Pydantic for data validation and settings management

#### Future Improvements
1. Add support for image recognition of ingredients
2. Implement nutritional analysis for recipes
3. Add user accounts for personalized recipe history
4. Integrate with grocery delivery services

#### License
This project is licensed under the MIT License - see the LICENSE file for details.
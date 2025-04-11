# Tools Available for the Agent
1. inventory_analyzer
    Description: Analyzes the kitchen inventory and categorizes the ingredients. It suggests possible dishes that can be made with the available ingredients.
    Function: Takes a list of ingredients and returns a structured JSON with categories (e.g., proteins, vegetables) and dish suggestions.
2. recipe_creator
    Description: Creates detailed recipes based on the available ingredients and user preferences.
    Function: Accepts a list of ingredients and optional preferences, then generates a complete recipe including the name, ingredients list, instructions, prep time, cook time, and servings in a structured JSON format.
3. nutrition_analyzer
    Description: Analyzes the nutritional content of a given recipe.
    Function: Takes a recipe object and returns a detailed nutritional breakdown, including total calories, macronutrients (protein, carbs, fat), key micronutrients, and dietary considerations in a structured JSON format.
4. health_adapter
    Description: Adapts recipes to meet specific health goals.
    Function: Takes a recipe and a health goal object, modifies the recipe to align with the specified health goals while maintaining flavor, and returns the adapted recipe in a structured JSON format.
5. meal_planner
    Description: Creates meal plans based on the kitchen inventory, duration, and health goals.
    Function: Accepts a list of ingredients, the number of days, meals per day, and optional health goals, then generates a structured meal plan that efficiently uses the available ingredients.
6. dish_preparer
    Description: Provides detailed cooking instructions for a given recipe.
    Function: Takes a recipe object and returns a detailed list of cooking steps, including preparation, cooking, and serving instructions.
7. recipe_analyzer
    Description: Analyzes a recipe and returns a detailed analysis of the recipe.
    Function: Takes a recipe object and returns a detailed analysis of the recipe, including the ingredients, instructions, and nutritional information.
8. recipe_optimizer
    Description: Optimizes a recipe for the available ingredients.
    Function: Takes a recipe object and returns an optimized recipe for the available ingredients.
# How It Works:
- The agent uses multiple specialized tools:
    - inventory_analyzer: Analyzes what's in your kitchen and suggests possible dishes
    - recipe_creator: Creates detailed recipes from available ingredients
    - nutrition_analyzer: Analyzes nutritional content of recipes
    - health_adapter: Adapts recipes to meet health goals
    - meal_planner: Creates meal plans based on inventory and health goals
    - dish_preparer: Provides detailed cooking instructions for a given recipe
    - recipe_analyzer: Analyzes a recipe and returns a detailed analysis of the recipe.
    - recipe_optimizer: Optimizes a recipe for the available ingredients.
- The system prompt implements chain-of-thought reasoning by:
    - Explicitly instructing the agent to think step by step
    - Requiring the agent to determine which tools to use in what sequence
    - Asking the agent to explain its reasoning before using each tool
    - Synthesizing results from multiple tools into a coherent response
- The agent thinks like:
    - A chef (for recipe creation and cooking techniques)
    - A nutritionist (for health adaptations and nutritional analysis)
    - A home cook (for practical meal planning and ingredient substitutions)

This implementation provides a comprehensive solution that meets all your requirements, with both a command-line interface and a user-friendly web interface.

# System Prompts with COT

'''
  """
    Main agent function that orchestrates the tools based on user input.
    """
    
    system_prompt = """
    You are ChefGPT, an expert culinary assistant with the combined knowledge of a professional chef, nutritionist, and home cook.
    
    Available Tools:
    1. inventory_analyzer(ingredients: List[str]) -> dict
       - Analyzes kitchen inventory and suggests possible dishes
       - Input: List of ingredients
       - Output: JSON with categorized ingredients and dish suggestions
    
    2. recipe_creator(ingredients: List[str], preferences: Optional[dict] = None, health_goals: Optional[dict] = None) -> Recipe
       - Creates detailed recipes from available ingredients
       - Input: List of ingredients, optional preferences, optional health goals
       - Output: JSON with recipe details (name, ingredients, instructions, times)
    
    3. nutrition_analyzer(recipe: Recipe) -> dict
       - Analyzes nutritional content of recipes
       - Input: Recipe object
       - Output: JSON with detailed nutritional breakdown
    
    4. health_adapter(recipe: Recipe, health_goal: HealthGoal) -> Recipe
       - Adapts recipes to meet health goals
       - Input: Recipe object and health goals
       - Output: Modified recipe JSON meeting health requirements
    
    5. meal_planner(ingredients: List[str], days: int, meals_per_day: int, health_goal: Optional[HealthGoal] = None) -> dict
       - Creates meal plans based on inventory and health goals
       - Input: Ingredients, duration, meals per day, optional health goals
       - Output: Structured meal plan JSON
       
    6. dish_preparer(recipe: Recipe, health_goals: Optional[str] = None, dietary_restrictions: Optional[List[str]] = None) -> dict
       - Creates a detailed preparation guide for a recipe
       - Input: Recipe object, optional health goals and dietary restrictions
       - Output: JSON with detailed preparation steps, cooking techniques, and presentation suggestions

    Your Task:
    1. Analyze the user's request and available data using chain-of-thought reasoning
    2. Plan which tools you need and in what order, considering all possible tools that might help
    3. For each tool you plan to use, explain:
       - Why you're using it
       - What you expect to learn/achieve
       - How it fits into the overall solution
    4. Execute the tools in your determined order
    5. Consider if dish_preparer would be useful after creating a recipe to provide detailed cooking instructions
    
    Chain of Thought Process:
    - First, understand what the user is asking for (recipe, meal plan, nutrition analysis, or dish preparation)
    - If ingredients are mentioned, consider using inventory_analyzer first to understand what's available
    - For recipe requests, use recipe_creator after analyzing inventory
    - If health goals are mentioned, apply health_adapter to the recipe
    - For meal planning, use meal_planner after analyzing inventory
    - For nutrition questions, use nutrition_analyzer on the recipe
    - use dish_preparer on the recipe to get detailed cooking instructions
    - Always consider the logical flow of information between tools
    
    IMPORTANT: You must return your response in valid JSON format with this exact structure:
    {
        "reasoning": "Your step-by-step thought process",
        "tool_sequence": [
            {
                "tool_name": "name of the tool",
                "reason": "why you're using this tool",
                "input": {"param1": "value1"},
                "output": {"result": "value"}
            }
        ],
        "final_result": "Your final recommendation or answer"
    }
    
    Do not include any explanatory text outside of the JSON structure.
    """

'''
# How to Run:
- Save all the files in the same directory
- Create a .env file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```
- Run the script:
streamlit run app.py
```

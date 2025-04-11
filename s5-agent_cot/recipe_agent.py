import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import openai
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define data models
class Ingredient(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    
class Recipe(BaseModel):
    name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    nutrition: Optional[Dict[str, Any]] = None

class HealthGoal(BaseModel):
    goal_type: str = Field(..., description="Type of health goal (e.g., 'weight_loss', 'muscle_gain', 'heart_health')")
    restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions (e.g., 'gluten-free', 'dairy-free')")
    target_calories: Optional[int] = None
    target_protein: Optional[int] = None
    target_carbs: Optional[int] = None
    target_fat: Optional[int] = None

class MealPlan(BaseModel):
    days: int
    meals_per_day: int
    recipes: List[Dict[str, Any]]
    nutrition_summary: Optional[Dict[str, Any]] = None

# Tool functions
def inventory_analyzer(inventory: List[str]) -> Dict[str, Any]:
    """Analyzes kitchen inventory and categorizes ingredients."""
    
    prompt = f"""
    As a professional chef, analyze the following kitchen inventory and categorize the ingredients:
    
    Inventory: {', '.join(inventory)}
    
    Categorize these ingredients into:
    1. Proteins
    2. Vegetables
    3. Fruits
    4. Grains/Starches
    5. Dairy
    6. Herbs/Spices
    7. Other
    
    Then, identify 3-5 potential dish types that could be made with these ingredients.
    Provide your response as a structured JSON with categories and dish suggestions.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a professional chef who analyzes ingredients and suggests dishes."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return eval(response.choices[0].message.content)

def recipe_creator(ingredients: List[str], preferences: Optional[Dict[str, Any]] = None, health_goals: Optional[Dict[str, Any]] = None) -> Recipe:
    """Creates a recipe based on available ingredients, preferences, and health goals."""
    
    pref_text = ""
    if preferences:
        if isinstance(preferences, dict):
            pref_text = f"Preferences: {preferences.get('description', '')}"
        else:
            pref_text = f"Preferences: {preferences}"
    
    health_text = ""
    if health_goals:
        goal_type = health_goals.get("goal_type")
        restrictions = health_goals.get("restrictions")
        
        if goal_type:
            health_text += f"\nHealth Goal: {goal_type}"
        
        if restrictions:
            health_text += f"\nDietary Restrictions: {', '.join(restrictions)}"
    
    prompt = f"""
    As a creative chef, create a detailed recipe using some or all of these ingredients:
    
    Ingredients: {', '.join(ingredients)}
    {pref_text}
    {health_text}
    
    Provide a complete recipe with:
    1. Recipe name
    2. Ingredients list with quantities
    3. Step-by-step instructions
    4. Estimated prep and cook times
    5. Number of servings
    
    IMPORTANT: Your response MUST be a valid JSON object with EXACTLY this structure:
    {{
      "name": "Recipe Name",
      "ingredients": [
        {{"name": "ingredient1", "quantity": "1", "unit": "cup"}},
        {{"name": "ingredient2", "quantity": "2", "unit": "tablespoons"}}
      ],
      "instructions": ["Step 1", "Step 2", "Step 3"],
      "prep_time": 15,
      "cook_time": 30,
      "servings": 4
    }}
    
    Do not include any text outside of this JSON structure.
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a creative chef who creates delicious recipes from available ingredients. You MUST return valid JSON in the exact format requested without any nested objects or explanatory text."},
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        recipe_data = json.loads(response.choices[0].message.content)
        
        # Check if the response has a nested 'recipe' object
        if 'recipe' in recipe_data:
            recipe_data = recipe_data['recipe']
        
        # Ensure ingredients are properly formatted
        if 'ingredients' in recipe_data and isinstance(recipe_data['ingredients'], list):
            for i, ingredient in enumerate(recipe_data['ingredients']):
                if isinstance(ingredient, str):
                    # Convert string ingredients to proper format
                    parts = ingredient.split(' ', 1)
                    if len(parts) > 1:
                        quantity = parts[0]
                        name = parts[1]
                        recipe_data['ingredients'][i] = {"name": name, "quantity": quantity, "unit": ""}
                    else:
                        recipe_data['ingredients'][i] = {"name": ingredient, "quantity": "", "unit": ""}
        
        return Recipe(**recipe_data)
    except Exception as e:
        print(f"Error parsing recipe data: {e}")
        print(f"Raw response: {response.choices[0].message.content}")
        
        # Create a minimal valid recipe as fallback
        return Recipe(
            name=f"Quick {ingredients[0].capitalize()} Recipe",
            ingredients=[Ingredient(name=ing) for ing in ingredients],
            instructions=["Combine all ingredients", "Cook until done", "Serve and enjoy"]
        )

def nutrition_analyzer(recipe: Recipe) -> Dict[str, Any]:
    """Analyzes the nutritional content of a recipe."""
    
    ingredients_text = "\n".join([f"- {i.quantity or ''} {i.unit or ''} {i.name}" for i in recipe.ingredients])
    
    prompt = f"""
    As a nutritionist, analyze the following recipe and provide a detailed nutritional breakdown:
    
    Recipe: {recipe.name}
    
    Ingredients:
    {ingredients_text}
    
    Provide a nutritional analysis including:
    1. Total calories
    2. Macronutrients (protein, carbs, fat)
    3. Key micronutrients
    4. Dietary considerations (gluten-free, dairy-free, etc.)
    
    Format your response as a structured JSON with the following format:
    {{
      "calories": "500 kcal",
      "protein": "30g",
      "carbs": "45g",
      "fat": "15g",
      "fiber": "5g",
      "sugar": "10g",
      "vitamins": ["Vitamin A", "Vitamin C"],
      "minerals": ["Iron", "Calcium"],
      "dietary_considerations": ["gluten-free", "dairy-free"]
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a nutritionist who analyzes recipes for their nutritional content. Return JSON in the exact format requested."},
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        nutrition_data = json.loads(response.choices[0].message.content)
        return nutrition_data
    except Exception as e:
        print(f"Error parsing nutrition data: {e}")
        print(f"Raw response: {response.choices[0].message.content}")
        
        # Return a minimal valid nutrition object as fallback
        return {
            "calories": "Not available",
            "protein": "Not available",
            "carbs": "Not available",
            "fat": "Not available",
            "note": "Nutrition analysis failed, please try again."
        }

def health_adapter(recipe: Recipe, health_goal: HealthGoal) -> Recipe:
    """Adapts a recipe to meet specific health goals."""
    
    ingredients_text = "\n".join([f"- {i.quantity or ''} {i.unit or ''} {i.name}" for i in recipe.ingredients])
    instructions_text = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(recipe.instructions)])
    
    prompt = f"""
    As a nutritionist and chef, adapt this recipe to meet the following health goals:
    
    Recipe: {recipe.name}
    
    Ingredients:
    {ingredients_text}
    
    Instructions:
    {instructions_text}
    
    Health Goals:
    - Type: {health_goal.goal_type}
    - Restrictions: {', '.join(health_goal.restrictions) if health_goal.restrictions else 'None'}
    - Target calories: {health_goal.target_calories or 'Not specified'}
    - Target protein: {health_goal.target_protein or 'Not specified'}g
    - Target carbs: {health_goal.target_carbs or 'Not specified'}g
    - Target fat: {health_goal.target_fat or 'Not specified'}g
    
    Modify the recipe to better align with these health goals while maintaining flavor.
    
    Format your response as a structured JSON with the following format:
    {{
      "name": "Recipe Name",
      "ingredients": [
        {{"name": "ingredient1", "quantity": "1", "unit": "cup"}},
        {{"name": "ingredient2", "quantity": "2", "unit": "tablespoons"}}
      ],
      "instructions": ["Step 1", "Step 2", "Step 3"],
      "prep_time": 15,
      "cook_time": 30,
      "servings": 4
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a nutritionist and chef who adapts recipes to meet health goals. Return JSON in the exact format requested without any nested objects."},
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        recipe_data = json.loads(response.choices[0].message.content)
        
        # Check if the response has a nested 'recipe' object
        if 'recipe' in recipe_data:
            recipe_data = recipe_data['recipe']
            
        # Ensure ingredients are properly formatted
        if 'ingredients' in recipe_data and isinstance(recipe_data['ingredients'], list):
            for i, ingredient in enumerate(recipe_data['ingredients']):
                if isinstance(ingredient, str):
                    # Convert string ingredients to proper format
                    parts = ingredient.split(' ', 1)
                    if len(parts) > 1:
                        quantity = parts[0]
                        name = parts[1]
                        recipe_data['ingredients'][i] = {"name": name, "quantity": quantity, "unit": ""}
                    else:
                        recipe_data['ingredients'][i] = {"name": ingredient, "quantity": "", "unit": ""}
        
        return Recipe(**recipe_data)
    except Exception as e:
        print(f"Error parsing adapted recipe data: {e}")
        # Return the original recipe if adaptation fails
        return recipe

def meal_planner(inventory: List[str], days: int, meals_per_day: int, health_goal: Optional[HealthGoal] = None) -> MealPlan:
    """Creates a meal plan based on inventory, duration, and health goals."""
    
    health_goal_text = ""
    if health_goal:
        health_goal_text = f"""
        Health Goals:
        - Type: {health_goal.goal_type}
        - Restrictions: {', '.join(health_goal.restrictions) if health_goal.restrictions else 'None'}
        - Target calories: {health_goal.target_calories or 'Not specified'}
        - Target protein: {health_goal.target_protein or 'Not specified'}g
        - Target carbs: {health_goal.target_carbs or 'Not specified'}g
        - Target fat: {health_goal.target_fat or 'Not specified'}g
        """
    
    prompt = f"""
    As a meal planning expert, create a {days}-day meal plan with {meals_per_day} meals per day using these ingredients:
    
    Ingredients: {', '.join(inventory)}
    
    {health_goal_text}
    
    For each meal, provide:
    1. Recipe name
    2. Brief description
    3. Main ingredients used
    4. Estimated nutrition
    
    Create a varied and balanced meal plan that efficiently uses the available ingredients.
    Format your response as a structured JSON that can be parsed into a MealPlan object.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a meal planning expert who creates efficient and balanced meal plans."},
            {"role": "user", "content": prompt}
        ]
    )
    
    meal_plan_data = eval(response.choices[0].message.content)
    return MealPlan(**meal_plan_data)

def dish_preparer(recipe, health_goals=None, dietary_restrictions=None):
    """
    Prepares a dish based on a recipe, adapting it for health goals and dietary restrictions.
    
    Args:
        recipe: The recipe to prepare
        health_goals: Optional health goals to consider
        dietary_restrictions: Optional dietary restrictions to follow
        
    Returns:
        A detailed preparation guide with cooking tips, timing, and presentation suggestions
    """
    # Create a prompt for the LLM
    prompt = f"""
    You are a professional chef preparing the following recipe:
    
    Recipe: {recipe.name}
    
    Ingredients:
    {', '.join([f"{getattr(ing, 'quantity', '')} {getattr(ing, 'unit', '')} {getattr(ing, 'name', str(ing))}" 
               if not isinstance(ing, dict) else f"{ing.get('quantity', '')} {ing.get('unit', '')} {ing.get('name', '')}" 
               for ing in recipe.ingredients])}
    
    Instructions:
    {' '.join([f"{i+1}. {step}" for i, step in enumerate(recipe.instructions)])}
    
    Please provide a detailed preparation guide that includes:
    1. A catchy name for this dish preparation method (e.g., "Chef's Perfect Sear Technique")
    2. Preparation steps with precise timing and temperatures
    3. Cooking techniques and tips for best results
    4. Common mistakes to avoid
    5. Presentation suggestions with plating details
    6. Serving recommendations (temperature, accompaniments)
    7. Storage instructions if there are leftovers
    
    Format your response to be visually appealing with clear sections and helpful tips.
    """
    
    if health_goals:
        prompt += f"\n\nPlease adapt the preparation to support these health goals: {health_goals}"
    
    if dietary_restrictions:
        prompt += f"\n\nEnsure the preparation follows these dietary restrictions: {', '.join(dietary_restrictions)}"
    
    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a professional chef providing detailed cooking instructions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    preparation_guide = response.choices[0].message.content
    
    # Extract a technique name from the first line if possible
    technique_name = "Chef's Preparation Guide"
    lines = preparation_guide.split('\n')
    if lines and len(lines[0]) < 100 and ("#" in lines[0] or ":" in lines[0] or "technique" in lines[0].lower() or "method" in lines[0].lower()):
        technique_name = lines[0].replace("#", "").strip()
    
    return {
        "recipe_name": recipe.name,
        "technique_name": technique_name,
        "preparation_guide": preparation_guide,
        "health_considerations": health_goals,
        "dietary_restrictions": dietary_restrictions
    }

def chef_agent(user_input: str) -> Dict[str, Any]:
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
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Upgraded to GPT-4o for better reasoning
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        try:
            # Try to parse as JSON
            result = json.loads(response.choices[0].message.content)
            
            # Process tool_sequence to ensure outputs are properly formatted
            if "tool_sequence" in result:
                for i, step in enumerate(result["tool_sequence"]):
                    if "output" in step and isinstance(step["output"], str):
                        # Try to parse string output as JSON
                        try:
                            result["tool_sequence"][i]["output"] = json.loads(step["output"])
                        except:
                            # If parsing fails, keep as string but wrap in a dict
                            result["tool_sequence"][i]["output"] = {"text_output": step["output"]}
            
            # Modify tool_sequence to include health goals
            if "tool_sequence" in result:
                for i, step in enumerate(result["tool_sequence"]):
                    if step["tool_name"] == "recipe_creator":
                        # Extract health goals from the input if available
                        input_params = step.get("input", {})
                        if "health_goals" not in input_params and "health_goal" in user_input.lower():
                            # Try to extract health goals from the query
                            try:
                                query_data = json.loads(user_input)
                                if "health_goals" in query_data:
                                    input_params["health_goals"] = query_data["health_goals"]
                                    result["tool_sequence"][i]["input"] = input_params
                            except:
                                pass
            
            return result
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return a formatted fallback response
            content = response.choices[0].message.content
            print(f"JSON parse error: {e}")
            print(f"Raw content: {content}")
            return {
                "reasoning": "Direct response from assistant (JSON parsing failed)",
                "tool_sequence": [],
                "final_result": content
            }
    except Exception as e:
        # Handle any API errors
        print(f"Error calling OpenAI API: {str(e)}")
        return {
            "reasoning": f"Error occurred: {str(e)}",
            "tool_sequence": [],
            "final_result": f"Sorry, an error occurred: {str(e)}"
        }

# Example usage
if __name__ == "__main__":
    user_query = "I have chicken, rice, bell peppers, onions, garlic, and some spices. Can you create a recipe and suggest a meal plan for 2 days? I'm trying to build muscle and need high protein meals."
    result = chef_agent(user_query)
    print(result) 
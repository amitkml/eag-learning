"""
Action Module - Handles executing actions and generating outputs
"""
from typing import Dict, List, Any, Optional
import json

class ActionModule:
    def __init__(self, client):
        """Initialize the action module with OpenAI client"""
        self.client = client
    
    def generate_detailed_recipe(self, recipe_option: Dict) -> Dict:
        """Generate a detailed recipe with instructions from a recipe option"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional chef. Create a detailed recipe with step-by-step instructions, cooking tips, and presentation suggestions."},
                {"role": "user", "content": f"Create a detailed recipe for: {recipe_option['name']}. Ingredients: {', '.join(recipe_option['ingredients'])}. Format your response as JSON."}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            result = response.choices[0].message.content
            detailed_recipe = json.loads(result)
            
            # Merge with original recipe option data
            for key, value in recipe_option.items():
                if key not in detailed_recipe:
                    detailed_recipe[key] = value
            
            return detailed_recipe
        except Exception as e:
            print(f"Error generating detailed recipe: {e}")
            return recipe_option
    
    def generate_shopping_list(self, meal_plan: List[Dict], available_ingredients: List[Dict]) -> List[Dict]:
        """Generate a shopping list based on a meal plan and available ingredients"""
        # Convert available ingredients to a simple list of names for comparison
        available = [i.get("name", "").lower() for i in available_ingredients]
        
        # Extract all ingredients from the meal plan
        all_ingredients = []
        for day in meal_plan:
            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_type, {})
                if meal and "ingredients" in meal:
                    all_ingredients.extend(meal["ingredients"])
            
            for snack in day.get("snacks", []):
                if "ingredients" in snack:
                    all_ingredients.extend(snack["ingredients"])
        
        # Identify missing ingredients
        missing_ingredients = []
        for ingredient in all_ingredients:
            # Check if this ingredient or a similar one is available
            ingredient_name = ingredient.lower() if isinstance(ingredient, str) else ingredient.get("name", "").lower()
            
            if not any(available_ing in ingredient_name or ingredient_name in available_ing for available_ing in available):
                # Check if it's already in our missing list
                if not any(missing.get("name", "").lower() == ingredient_name for missing in missing_ingredients):
                    if isinstance(ingredient, str):
                        missing_ingredients.append({"name": ingredient, "quantity": "as needed"})
                    else:
                        missing_ingredients.append(ingredient)
        
        return missing_ingredients
    
    def format_recipe_output(self, recipe: Dict) -> str:
        """Format a recipe for display"""
        output = []
        
        # Title
        output.append(f"# {recipe.get('name', 'Recipe')}")
        output.append("")
        
        # Basic info
        if recipe.get('preparation_time'):
            output.append(f"**Prep Time:** {recipe['preparation_time']}")
        if recipe.get('difficulty'):
            output.append(f"**Difficulty:** {recipe['difficulty']}")
        if recipe.get('estimated_calories'):
            output.append(f"**Calories:** {recipe['estimated_calories']} kcal")
        output.append("")
        
        # Ingredients
        output.append("## Ingredients")
        for ingredient in recipe.get('ingredients', []):
            if isinstance(ingredient, str):
                output.append(f"- {ingredient}")
            else:
                quantity = ingredient.get('quantity', '')
                unit = ingredient.get('unit', '')
                name = ingredient.get('name', '')
                output.append(f"- {quantity} {unit} {name}".strip())
        output.append("")
        
        # Instructions
        output.append("## Instructions")
        instructions = recipe.get('instructions', [])
        if isinstance(instructions, list):
            for i, step in enumerate(instructions, 1):
                output.append(f"{i}. {step}")
        else:
            output.append(instructions)
        output.append("")
        
        # Tips
        if recipe.get('tips'):
            output.append("## Chef's Tips")
            tips = recipe.get('tips', [])
            if isinstance(tips, list):
                for tip in tips:
                    output.append(f"- {tip}")
            else:
                output.append(tips)
        
        return "\n".join(output)
    
    def format_meal_plan_output(self, meal_plan: List[Dict]) -> str:
        """Format a meal plan for display"""
        output = []
        
        output.append("# Your Meal Plan")
        output.append("")
        
        for i, day in enumerate(meal_plan, 1):
            output.append(f"## Day {i}")
            output.append("")
            
            # Breakfast
            if day.get('breakfast'):
                output.append("### Breakfast")
                output.append(f"**{day['breakfast'].get('name', 'Breakfast')}**")
                if day['breakfast'].get('estimated_calories'):
                    output.append(f"*{day['breakfast']['estimated_calories']} calories*")
                output.append("")
            
            # Lunch
            if day.get('lunch'):
                output.append("### Lunch")
                output.append(f"**{day['lunch'].get('name', 'Lunch')}**")
                if day['lunch'].get('estimated_calories'):
                    output.append(f"*{day['lunch']['estimated_calories']} calories*")
                output.append("")
            
            # Dinner
            if day.get('dinner'):
                output.append("### Dinner")
                output.append(f"**{day['dinner'].get('name', 'Dinner')}**")
                if day['dinner'].get('estimated_calories'):
                    output.append(f"*{day['dinner']['estimated_calories']} calories*")
                output.append("")
            
            # Snacks
            if day.get('snacks'):
                output.append("### Snacks")
                for snack in day['snacks']:
                    output.append(f"- **{snack.get('name', 'Snack')}**")
                    if snack.get('estimated_calories'):
                        output.append(f"  *{snack['estimated_calories']} calories*")
                output.append("")
            
            # Daily total
            if day.get('total_calories'):
                output.append(f"**Daily Total:** {day['total_calories']} calories")
            
            output.append("\n---\n")
        
        return "\n".join(output)
    
    def format_shopping_list(self, shopping_list: List[Dict]) -> str:
        """Format a shopping list for display"""
        output = ["# Shopping List", ""]
        
        # Group by category if available
        categorized = {}
        uncategorized = []
        
        for item in shopping_list:
            if isinstance(item, str):
                uncategorized.append(item)
            else:
                category = item.get('category', 'Other')
                if category not in categorized:
                    categorized[category] = []
                
                quantity = item.get('quantity', '')
                unit = item.get('unit', '')
                name = item.get('name', '')
                
                formatted = f"{quantity} {unit} {name}".strip()
                categorized[category].append(formatted)
        
        # Output categorized items
        for category, items in categorized.items():
            output.append(f"## {category}")
            for item in items:
                output.append(f"- {item}")
            output.append("")
        
        # Output uncategorized items
        if uncategorized:
            output.append("## Other Items")
            for item in uncategorized:
                output.append(f"- {item}")
        
        return "\n".join(output) 
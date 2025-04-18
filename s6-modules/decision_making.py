"""
Decision-Making Module - Handles reasoning and planning
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class RecipeOption(BaseModel):
    """Model for a recipe option"""
    name: str
    ingredients: List[str]
    missing_ingredients: List[str] = Field(default_factory=list)
    preparation_time: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_calories: Optional[int] = None
    suitability_score: Optional[float] = None  # 0-10 score for how well it matches preferences

class MealPlanDay(BaseModel):
    """Model for a day in a meal plan"""
    breakfast: Optional[Dict] = None
    lunch: Optional[Dict] = None
    dinner: Optional[Dict] = None
    snacks: List[Dict] = Field(default_factory=list)
    total_calories: Optional[int] = None

class DecisionMakingModule:
    def __init__(self, client):
        """Initialize the decision making module with OpenAI client"""
        self.client = client
    
    def generate_recipe_options(
        self, 
        available_ingredients: List[Dict], 
        user_preferences: Dict,
        num_options: int = 3
    ) -> List[RecipeOption]:
        """Generate recipe options based on available ingredients and preferences"""
        ingredients_str = ", ".join([i.get("name", "") for i in available_ingredients])
        
        # Format preferences for the prompt
        pref_parts = []
        if user_preferences.get("diet_type"):
            pref_parts.append(f"Diet: {user_preferences['diet_type']}")
        if user_preferences.get("allergies"):
            pref_parts.append(f"Allergies: {', '.join(user_preferences['allergies'])}")
        if user_preferences.get("health_goals"):
            pref_parts.append(f"Health goals: {user_preferences['health_goals']}")
        if user_preferences.get("disliked_ingredients"):
            pref_parts.append(f"Dislikes: {', '.join(user_preferences['disliked_ingredients'])}")
        if user_preferences.get("calorie_target"):
            pref_parts.append(f"Calorie target: {user_preferences['calorie_target']}")
        
        preferences_str = ". ".join(pref_parts)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative chef who can suggest recipe options based on available ingredients. For each recipe, include name, ingredients list, missing ingredients, preparation time, difficulty, and estimated calories."},
                {"role": "user", "content": f"I have these ingredients: {ingredients_str}. My preferences are: {preferences_str}. Suggest {num_options} recipe options. Format your response as JSON."}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            result = response.choices[0].message.content
            import json
            parsed = json.loads(result)
            
            recipe_options = []
            for recipe_data in parsed.get("recipes", []):
                recipe = RecipeOption(
                    name=recipe_data.get("name", ""),
                    ingredients=recipe_data.get("ingredients", []),
                    missing_ingredients=recipe_data.get("missing_ingredients", []),
                    preparation_time=recipe_data.get("preparation_time"),
                    difficulty=recipe_data.get("difficulty"),
                    estimated_calories=recipe_data.get("estimated_calories"),
                    suitability_score=recipe_data.get("suitability_score")
                )
                recipe_options.append(recipe)
            
            return recipe_options
        except Exception as e:
            print(f"Error generating recipe options: {e}")
            return []
    
    def create_meal_plan(
        self, 
        available_ingredients: List[Dict],
        user_preferences: Dict,
        days: int = 1
    ) -> List[MealPlanDay]:
        """Create a meal plan for a specified number of days"""
        ingredients_str = ", ".join([i.get("name", "") for i in available_ingredients])
        
        # Format preferences for the prompt
        pref_parts = []
        if user_preferences.get("diet_type"):
            pref_parts.append(f"Diet: {user_preferences['diet_type']}")
        if user_preferences.get("allergies"):
            pref_parts.append(f"Allergies: {', '.join(user_preferences['allergies'])}")
        if user_preferences.get("health_goals"):
            pref_parts.append(f"Health goals: {user_preferences['health_goals']}")
        if user_preferences.get("disliked_ingredients"):
            pref_parts.append(f"Dislikes: {', '.join(user_preferences['disliked_ingredients'])}")
        if user_preferences.get("calorie_target"):
            pref_parts.append(f"Calorie target: {user_preferences['calorie_target']}")
        
        preferences_str = ". ".join(pref_parts)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a meal planning expert. Create a {days}-day meal plan with breakfast, lunch, dinner, and snacks based on available ingredients and preferences. For each meal, include recipe name, ingredients, preparation instructions, and estimated calories."},
                {"role": "user", "content": f"I have these ingredients: {ingredients_str}. My preferences are: {preferences_str}. Create a {days}-day meal plan. Format your response as JSON."}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            result = response.choices[0].message.content
            import json
            parsed = json.loads(result)
            
            meal_plan = []
            for day_data in parsed.get("meal_plan", []):
                day = MealPlanDay(
                    breakfast=day_data.get("breakfast"),
                    lunch=day_data.get("lunch"),
                    dinner=day_data.get("dinner"),
                    snacks=day_data.get("snacks", []),
                    total_calories=day_data.get("total_calories")
                )
                meal_plan.append(day)
            
            return meal_plan
        except Exception as e:
            print(f"Error creating meal plan: {e}")
            return []
    
    def adjust_recipe(
        self,
        recipe: Dict,
        adjustment_type: str,  # "healthier", "faster", "vegetarian", etc.
        user_preferences: Dict
    ) -> Dict:
        """Adjust a recipe based on specified criteria"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a recipe adaptation expert. Modify the given recipe to make it {adjustment_type}, while considering the user's preferences."},
                {"role": "user", "content": f"Recipe: {json.dumps(recipe)}. User preferences: {json.dumps(user_preferences)}. Please adapt this recipe to make it {adjustment_type}. Format your response as JSON."}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            result = response.choices[0].message.content
            import json
            adjusted_recipe = json.loads(result)
            return adjusted_recipe
        except Exception as e:
            print(f"Error adjusting recipe: {e}")
            return recipe 
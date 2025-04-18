"""
ChefChainAgent - Main agent that orchestrates the cooking and meal planning process
"""
from typing import Dict, List, Any, Optional, Union
import json
import os
from openai import OpenAI
import instructor
from instructor import OpenAISchema
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv

from perception import PerceptionModule, IngredientInfo, UserPreference
from memory import MemoryModule
from decision_making import DecisionMakingModule, RecipeOption, MealPlanDay
from action import ActionModule

# Load environment variables
load_dotenv(find_dotenv())

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

# Use instructor to enhance OpenAI client
client = instructor.patch(OpenAI(api_key=api_key))

class RecipeRequest(BaseModel):
    """Model for recipe request parameters"""
    ingredients: List[str] = Field(..., description="List of available ingredients")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User dietary preferences and restrictions")
    meal_type: Optional[str] = Field(None, description="Type of meal (breakfast, lunch, dinner, snack)")
    num_options: int = Field(3, description="Number of recipe options to generate")

class MealPlanRequest(BaseModel):
    """Model for meal plan request parameters"""
    ingredients: List[str] = Field(..., description="List of available ingredients")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User dietary preferences and restrictions")
    days: int = Field(1, description="Number of days to plan for")

class RecipeAdjustmentRequest(BaseModel):
    """Model for recipe adjustment request parameters"""
    recipe: Dict[str, Any] = Field(..., description="Original recipe to adjust")
    adjustment_type: str = Field(..., description="Type of adjustment (healthier, faster, vegetarian, etc.)")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User dietary preferences and restrictions")

class ChefChainAgent:
    def __init__(self):
        """Initialize the ChefChainAgent with its cognitive modules"""
        self.client = client
        self.perception = PerceptionModule(client)
        self.memory = MemoryModule()
        self.decision_making = DecisionMakingModule(client)
        self.action = ActionModule(client)
    
    def generate_recipe_options(self, request: RecipeRequest) -> List[Dict]:
        """Generate recipe options based on available ingredients and preferences"""
        # Parse ingredients
        ingredients = []
        for ing in request.ingredients:
            parsed = self.perception.parse_ingredients(ing)
            ingredients.extend(parsed)
        
        # Parse preferences if they're in text form
        if isinstance(request.preferences, str):
            preferences = self.perception.understand_preferences(request.preferences)
            preferences_dict = preferences.dict()
        else:
            preferences_dict = request.preferences
        
        # Store in memory
        self.memory.store_ingredients([ing.dict() for ing in ingredients])
        self.memory.store_user_preferences(preferences_dict)
        
        # Generate recipe options
        recipe_options = self.decision_making.generate_recipe_options(
            [ing.dict() for ing in ingredients],
            preferences_dict,
            request.num_options
        )
        
        return [option.dict() for option in recipe_options]
    
    def create_detailed_recipe(self, recipe_option: Dict) -> Dict:
        """Create a detailed recipe from a recipe option"""
        detailed_recipe = self.action.generate_detailed_recipe(recipe_option)
        self.memory.store_recipe(detailed_recipe)
        return detailed_recipe
    
    def create_meal_plan(self, request: MealPlanRequest) -> Dict:
        """Create a meal plan based on available ingredients and preferences"""
        # Parse ingredients
        ingredients = []
        for ing in request.ingredients:
            parsed = self.perception.parse_ingredients(ing)
            ingredients.extend(parsed)
        
        # Parse preferences if they're in text form
        if isinstance(request.preferences, str):
            preferences = self.perception.understand_preferences(request.preferences)
            preferences_dict = preferences.dict()
        else:
            preferences_dict = request.preferences
        
        # Store in memory
        self.memory.store_ingredients([ing.dict() for ing in ingredients])
        self.memory.store_user_preferences(preferences_dict)
        
        # Create meal plan
        meal_plan = self.decision_making.create_meal_plan(
            [ing.dict() for ing in ingredients],
            preferences_dict,
            request.days
        )
        
        # Generate shopping list
        shopping_list = self.action.generate_shopping_list(
            [day.dict() for day in meal_plan],
            [ing.dict() for ing in ingredients]
        )
        
        result = {
            "meal_plan": [day.dict() for day in meal_plan],
            "shopping_list": shopping_list
        }
        
        self.memory.store_meal_plan(result)
        return result
    
    def adjust_recipe(self, request: RecipeAdjustmentRequest) -> Dict:
        """Adjust a recipe based on specified criteria"""
        # Parse preferences if they're in text form
        if isinstance(request.preferences, str):
            preferences = self.perception.understand_preferences(request.preferences)
            preferences_dict = preferences.dict()
        else:
            preferences_dict = request.preferences
        
        # Adjust recipe
        adjusted_recipe = self.decision_making.adjust_recipe(
            request.recipe,
            request.adjustment_type,
            preferences_dict
        )
        
        self.memory.store_recipe(adjusted_recipe)
        return adjusted_recipe
    
    def format_recipe(self, recipe: Dict) -> str:
        """Format a recipe for display"""
        return self.action.format_recipe_output(recipe)
    
    def format_meal_plan(self, meal_plan: Dict) -> str:
        """Format a meal plan for display"""
        return self.action.format_meal_plan_output(meal_plan.get("meal_plan", []))
    
    def format_shopping_list(self, shopping_list: List[Dict]) -> str:
        """Format a shopping list for display"""
        return self.action.format_shopping_list(shopping_list) 
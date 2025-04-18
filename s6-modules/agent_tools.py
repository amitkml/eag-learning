"""
Agent Tools - Define the tools for the OpenAI Agent SDK
"""
from typing import Dict, List, Any, Optional
import json
from openai import OpenAI
from openai.types.beta.threads import Run
# Remove the problematic import
# from openai.types.beta.assistant import Tool
import instructor
from pydantic import BaseModel, Field

from chef_agent import ChefChainAgent, RecipeRequest, MealPlanRequest, RecipeAdjustmentRequest

# Initialize the ChefChainAgent
chef_agent = ChefChainAgent()

def generate_recipe_options_tool() -> Dict:
    """Define the generate recipe options tool"""
    return {
        "type": "function",
        "function": {
            "name": "generate_recipe_options",
            "description": "Generate recipe options based on available ingredients and preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of available ingredients"
                    },
                    "preferences": {
                        "type": "object",
                        "description": "User dietary preferences and restrictions"
                    },
                    "meal_type": {
                        "type": "string",
                        "description": "Type of meal (breakfast, lunch, dinner, snack)",
                        "enum": ["breakfast", "lunch", "dinner", "snack", "any"]
                    },
                    "num_options": {
                        "type": "integer",
                        "description": "Number of recipe options to generate",
                        "default": 3
                    }
                },
                "required": ["ingredients"]
            }
        }
    }

def create_detailed_recipe_tool() -> Dict:
    """Define the create detailed recipe tool"""
    return {
        "type": "function",
        "function": {
            "name": "create_detailed_recipe",
            "description": "Create a detailed recipe with instructions from a recipe option",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_option": {
                        "type": "object",
                        "description": "Recipe option to expand into a detailed recipe"
                    }
                },
                "required": ["recipe_option"]
            }
        }
    }

def create_meal_plan_tool() -> Dict:
    """Define the create meal plan tool"""
    return {
        "type": "function",
        "function": {
            "name": "create_meal_plan",
            "description": "Create a meal plan based on available ingredients and preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of available ingredients"
                    },
                    "preferences": {
                        "type": "object",
                        "description": "User dietary preferences and restrictions"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to plan for",
                        "default": 1
                    }
                },
                "required": ["ingredients"]
            }
        }
    }

def adjust_recipe_tool() -> Dict:
    """Define the adjust recipe tool"""
    return {
        "type": "function",
        "function": {
            "name": "adjust_recipe",
            "description": "Adjust a recipe based on specified criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe": {
                        "type": "object",
                        "description": "Original recipe to adjust"
                    },
                    "adjustment_type": {
                        "type": "string",
                        "description": "Type of adjustment (healthier, faster, vegetarian, etc.)",
                        "enum": ["healthier", "faster", "vegetarian", "vegan", "gluten-free", "low-carb", "high-protein", "low-calorie", "spicier", "milder"]
                    },
                    "preferences": {
                        "type": "object",
                        "description": "User dietary preferences and restrictions"
                    }
                },
                "required": ["recipe", "adjustment_type"]
            }
        }
    }

# Define the tool handlers
def handle_generate_recipe_options(params: Dict) -> Dict:
    """Handle the generate recipe options tool"""
    request = RecipeRequest(**params)
    return chef_agent.generate_recipe_options(request)

def handle_create_detailed_recipe(params: Dict) -> Dict:
    """Handle the create detailed recipe tool"""
    recipe_option = params.get("recipe_option", {})
    return chef_agent.create_detailed_recipe(recipe_option)

def handle_create_meal_plan(params: Dict) -> Dict:
    """Handle the create meal plan tool"""
    request = MealPlanRequest(**params)
    return chef_agent.create_meal_plan(request)

def handle_adjust_recipe(params: Dict) -> Dict:
    """Handle the adjust recipe tool"""
    request = RecipeAdjustmentRequest(**params)
    return chef_agent.adjust_recipe(request)

# Map tool names to handlers
TOOL_HANDLERS = {
    "generate_recipe_options": handle_generate_recipe_options,
    "create_detailed_recipe": handle_create_detailed_recipe,
    "create_meal_plan": handle_create_meal_plan,
    "adjust_recipe": handle_adjust_recipe
}

# Get all tools
def get_all_tools() -> List[Dict]:
    """Get all available tools"""
    return [
        generate_recipe_options_tool(),
        create_detailed_recipe_tool(),
        create_meal_plan_tool(),
        adjust_recipe_tool()
    ] 
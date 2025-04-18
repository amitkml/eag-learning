"""
Perception Module - Handles understanding user input and context
"""
from typing import Dict, List, Any, Optional
import openai
from pydantic import BaseModel, Field

class IngredientInfo(BaseModel):
    """Model for ingredient information"""
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    
class UserPreference(BaseModel):
    """Model for user dietary preferences and restrictions"""
    diet_type: Optional[str] = None  # e.g., "vegan", "keto", "paleo"
    allergies: List[str] = Field(default_factory=list)
    health_goals: Optional[str] = None  # e.g., "weight loss", "muscle gain"
    disliked_ingredients: List[str] = Field(default_factory=list)
    calorie_target: Optional[int] = None

class PerceptionModule:
    def __init__(self, client):
        """Initialize the perception module with OpenAI client"""
        self.client = client
    
    def parse_ingredients(self, ingredients_text: str) -> List[IngredientInfo]:
        """Parse raw ingredient text into structured data"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts ingredient information from text. Return a JSON array of ingredients with name, quantity, and unit when available."},
                {"role": "user", "content": f"Extract the ingredients from this text and format the response as JSON: {ingredients_text}"}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            result = response.choices[0].message.content
            import json
            parsed = json.loads(result)
            ingredients = []
            for item in parsed.get("ingredients", []):
                ingredients.append(IngredientInfo(
                    name=item.get("name", ""),
                    quantity=item.get("quantity"),
                    unit=item.get("unit")
                ))
            return ingredients
        except Exception as e:
            print(f"Error parsing ingredients: {e}")
            return []
    
    def understand_preferences(self, preferences_text: str) -> UserPreference:
        """Parse user preferences from text"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts dietary preferences and restrictions from text. Return a JSON object with diet_type, allergies, health_goals, disliked_ingredients, and calorie_target."},
                {"role": "user", "content": f"Extract the dietary preferences from this text and format the response as JSON: {preferences_text}"}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            result = response.choices[0].message.content
            import json
            parsed = json.loads(result)
            return UserPreference(
                diet_type=parsed.get("diet_type"),
                allergies=parsed.get("allergies", []),
                health_goals=parsed.get("health_goals"),
                disliked_ingredients=parsed.get("disliked_ingredients", []),
                calorie_target=parsed.get("calorie_target")
            )
        except Exception as e:
            print(f"Error parsing preferences: {e}")
            return UserPreference() 
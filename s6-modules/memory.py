"""
Memory Module - Handles storage and retrieval of information
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class MemoryModule:
    def __init__(self, memory_file: str = "memory.json"):
        """Initialize the memory module with a file for persistent storage"""
        self.memory_file = memory_file
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Load memory from file or initialize if it doesn't exist"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
                return self._initialize_memory()
        else:
            return self._initialize_memory()
    
    def _initialize_memory(self) -> Dict:
        """Initialize the memory structure"""
        return {
            "recipes": [],
            "user_preferences": {},
            "ingredients": [],
            "interactions": [],
            "enhanced_interactions": [],
            "perceptions": [],
            "decisions": [],
            "actions": [],
            "tool_calls": [],
            "meal_plans": []
        }
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def store_recipe(self, recipe: Dict) -> None:
        """Store a recipe in memory"""
        # Add timestamp
        recipe["timestamp"] = datetime.now().isoformat()
        
        # Check if recipe already exists (by name)
        for i, existing_recipe in enumerate(self.memory["recipes"]):
            if existing_recipe.get("name") == recipe.get("name"):
                # Update existing recipe
                self.memory["recipes"][i] = recipe
                self._save_memory()
                return
        
        # Add new recipe
        self.memory["recipes"].append(recipe)
        self._save_memory()
    
    def get_past_recipes(self) -> List[Dict]:
        """Get past recipes from memory"""
        return self.memory["recipes"]
    
    def store_user_preferences(self, preferences: Dict) -> None:
        """Store user preferences in memory"""
        # Add timestamp
        preferences["timestamp"] = datetime.now().isoformat()
        
        # Update preferences
        self.memory["user_preferences"] = preferences
        self._save_memory()
    
    def get_user_preferences(self) -> Dict:
        """Get user preferences from memory"""
        return self.memory["user_preferences"]
    
    def store_ingredients(self, ingredients: List[Dict]) -> None:
        """Store available ingredients in memory"""
        # Add timestamp
        ingredient_entry = {
            "ingredients": ingredients,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store ingredients
        self.memory["ingredients"] = ingredients
        self._save_memory()
    
    def get_available_ingredients(self) -> List[Dict]:
        """Get available ingredients from memory"""
        return self.memory["ingredients"]
    
    # New methods for storing cognitive layer outputs
    def store_perception(self, perception_data: Dict) -> None:
        """Store perception data in memory"""
        # Add timestamp
        perception_data["timestamp"] = datetime.now().isoformat()
        
        # Store perception
        self.memory["perceptions"].append(perception_data)
        self._save_memory()
    
    def store_decision(self, decision_data: Dict) -> None:
        """Store decision data in memory"""
        # Add timestamp
        decision_data["timestamp"] = datetime.now().isoformat()
        
        # Store decision
        self.memory["decisions"].append(decision_data)
        self._save_memory()
    
    def store_action(self, action_data: Dict) -> None:
        """Store action data in memory"""
        # Add timestamp
        action_data["timestamp"] = datetime.now().isoformat()
        
        # Store action
        self.memory["actions"].append(action_data)
        self._save_memory()
    
    def store_interaction(self, user_message: str, assistant_response: str) -> None:
        """Store a user-assistant interaction in memory"""
        interaction = {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory["interactions"].append(interaction)
        self._save_memory()
    
    def store_tool_call(self, tool_name: str, tool_input: Dict, tool_output: Dict) -> None:
        """Store a tool call in memory"""
        tool_call = {
            "tool_name": tool_name,
            "input": tool_input,
            "output": tool_output,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory["tool_calls"].append(tool_call)
        self._save_memory()
    
    def get_recent_perceptions(self, limit: int = 5) -> List[Dict]:
        """Get recent perception data"""
        return self.memory["perceptions"][-limit:]
    
    def get_recent_decisions(self, limit: int = 5) -> List[Dict]:
        """Get recent decision data"""
        return self.memory["decisions"][-limit:]
    
    def get_recent_actions(self, limit: int = 5) -> List[Dict]:
        """Get recent action data"""
        return self.memory["actions"][-limit:]
    
    def get_recent_interactions(self, limit: int = 5) -> List[Dict]:
        """Get recent user-assistant interactions"""
        return self.memory["interactions"][-limit:]
    
    def get_recent_tool_calls(self, limit: int = 5) -> List[Dict]:
        """Get recent tool calls"""
        return self.memory["tool_calls"][-limit:]
    
    def search_memory(self, query: str) -> Dict[str, List[Any]]:
        """Search memory for relevant information"""
        results = {
            "recipes": [],
            "interactions": [],
            "tool_calls": [],
            "perceptions": [],
            "decisions": [],
            "actions": []
        }
        
        # Search recipes
        for recipe in self.memory["recipes"]:
            if query.lower() in json.dumps(recipe).lower():
                results["recipes"].append(recipe)
        
        # Search interactions
        for interaction in self.memory["interactions"]:
            if query.lower() in interaction["user_message"].lower() or query.lower() in interaction["assistant_response"].lower():
                results["interactions"].append(interaction)
        
        # Search tool calls
        for tool_call in self.memory["tool_calls"]:
            if query.lower() in json.dumps(tool_call).lower():
                results["tool_calls"].append(tool_call)
        
        # Search perceptions
        for perception in self.memory["perceptions"]:
            if query.lower() in json.dumps(perception).lower():
                results["perceptions"].append(perception)
        
        # Search decisions
        for decision in self.memory["decisions"]:
            if query.lower() in json.dumps(decision).lower():
                results["decisions"].append(decision)
        
        # Search actions
        for action in self.memory["actions"]:
            if query.lower() in json.dumps(action).lower():
                results["actions"].append(action)
        
        return results
    
    def store_meal_plan(self, meal_plan: Dict) -> None:
        """Store a meal plan in memory"""
        # Add timestamp
        meal_plan["timestamp"] = datetime.now().isoformat()
        
        # Initialize meal_plans list if it doesn't exist
        if "meal_plans" not in self.memory:
            self.memory["meal_plans"] = []
        
        # Add the meal plan to memory
        self.memory["meal_plans"].append(meal_plan)
        
        # Save to file
        self._save_memory()
    
    def get_recent_meal_plans(self, limit: int = 5) -> List[Dict]:
        """Get recent meal plans"""
        if "meal_plans" not in self.memory:
            return []
        
        return self.memory["meal_plans"][-limit:]
    
    def store_enhanced_interaction(self, interaction_data: Dict) -> None:
        """Store an enhanced interaction with full conversation context"""
        # Add the interaction to memory
        self.memory["enhanced_interactions"].append(interaction_data)
        
        # Save to file
        self._save_memory()
    
    def get_recent_enhanced_interactions(self, limit: int = 5) -> List[Dict]:
        """Get recent enhanced interactions"""
        if "enhanced_interactions" not in self.memory:
            return []
        
        return self.memory["enhanced_interactions"][-limit:]
    
    def get_conversation_by_thread_id(self, thread_id: str) -> Optional[List[Dict]]:
        """Get all interactions for a specific thread"""
        if "enhanced_interactions" not in self.memory:
            return None
        
        # Filter interactions by thread_id
        thread_interactions = [
            interaction for interaction in self.memory["enhanced_interactions"]
            if interaction.get("thread_id") == thread_id
        ]
        
        return thread_interactions if thread_interactions else None 
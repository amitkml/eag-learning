from recipe_agent import (
    chef_agent, 
    inventory_analyzer, 
    recipe_creator, 
    nutrition_analyzer, 
    health_adapter, 
    meal_planner,
    HealthGoal
)

def main():
    print("🍳 Welcome to ChefGPT - Your AI Cooking Assistant! 🍳")
    print("I can help you create recipes, adapt them for health goals, and plan meals based on what's in your kitchen.")
    
    while True:
        print("\n" + "="*50)
        user_input = input("What can I help you with today? (type 'exit' to quit)\n> ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Thank you for using ChefGPT! Happy cooking!")
            break
        
        try:
            # Direct tool usage examples (for demonstration)
            if user_input.startswith("!analyze "):
                # Example: !analyze chicken, rice, tomatoes, onions
                inventory = [item.strip() for item in user_input[9:].split(',')]
                result = inventory_analyzer(inventory)
                print("\nInventory Analysis:")
                print(result)
                
            elif user_input.startswith("!recipe "):
                # Example: !recipe chicken, rice, tomatoes, onions
                ingredients = [item.strip() for item in user_input[8:].split(',')]
                result = recipe_creator(ingredients)
                print(f"\nRecipe: {result.name}")
                print("\nIngredients:")
                for ing in result.ingredients:
                    print(f"- {ing.quantity or ''} {ing.unit or ''} {ing.name}")
                print("\nInstructions:")
                for i, step in enumerate(result.instructions):
                    print(f"{i+1}. {step}")
                
            elif user_input.startswith("!plan "):
                # Example: !plan chicken, rice, tomatoes, onions | 2 | 3
                parts = user_input[6:].split('|')
                inventory = [item.strip() for item in parts[0].split(',')]
                days = int(parts[1].strip())
                meals = int(parts[2].strip()) if len(parts) > 2 else 3
                
                health_goal = None
                if len(parts) > 3:
                    health_goal = HealthGoal(
                        goal_type=parts[3].strip(),
                        restrictions=[r.strip() for r in parts[4].split(',')] if len(parts) > 4 else None
                    )
                
                result = meal_planner(inventory, days, meals, health_goal)
                print(f"\nMeal Plan for {days} days ({meals} meals per day):")
                print(result)
            
            # Use the main agent for all other queries
            else:
                result = chef_agent(user_input)
                print("\n" + result)
                
        except Exception as e:
            print(f"Sorry, I encountered an error: {str(e)}")
            print("Please try again with a different query.")

if __name__ == "__main__":
    main()

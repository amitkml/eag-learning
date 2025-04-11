import streamlit as st
from recipe_agent import (
    chef_agent, 
    recipe_creator, 
    health_adapter, 
    nutrition_analyzer,
    inventory_analyzer,
    dish_preparer,
    HealthGoal, 
    Ingredient,
    Recipe
)
import json
import time

# This must be the first Streamlit command
st.set_page_config(
    page_title="ChefGPT - AI Cooking Assistant",
    page_icon="🍳",
    layout="wide"
)

st.title("🍳 ChefGPT - Your AI Cooking Assistant")
st.subheader("Create recipes, adapt them for health goals, and plan meals based on what's in your kitchen")

# Initialize session state for storing results
if 'recipe_result' not in st.session_state:
    st.session_state.recipe_result = None
if 'meal_plan_result' not in st.session_state:
    st.session_state.meal_plan_result = None
if 'nutrition_result' not in st.session_state:
    st.session_state.nutrition_result = None
if 'inventory_analysis' not in st.session_state:
    st.session_state.inventory_analysis = None
if 'health_adapted_recipe' not in st.session_state:
    st.session_state.health_adapted_recipe = None
if 'tool_outputs' not in st.session_state:
    st.session_state.tool_outputs = []
if 'preparation_guide' not in st.session_state:
    st.session_state.preparation_guide = None

# Sidebar for inventory input
with st.sidebar:
    st.header("Your Kitchen Inventory")
    inventory_text = st.text_area(
        "List your ingredients (one per line):",
        height=200,
        placeholder="chicken\nrice\nonions\ngarlic\nbell peppers\ntomatoes\nolive oil\nsalt\npepper"
    )
    
    st.header("Health Goals (Optional)")
    goal_type = st.selectbox(
        "Health Goal:",
        ["None", "Weight Loss", "Muscle Gain", "Heart Health", "Diabetes Management", "General Health"]
    )
    
    restrictions = st.multiselect(
        "Dietary Restrictions:",
        ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut-Free", "Low-Carb", "Low-Fat", "Low-Sodium"]
    )
    
    use_health_goals = goal_type != "None" or restrictions

# Main content area
tab1, tab2, tab3 = st.tabs(["Recipe Creator", "Meal Planner", "Nutrition Analyzer"])

with tab1:
    st.header("Create a Recipe")
    recipe_preferences = st.text_area(
        "Any specific preferences for your recipe? (cuisine, cooking method, etc.)",
        placeholder="I'd like a quick stir-fry with Asian flavors"
    )
    
    # Add a checkbox to show tool outputs
    show_tool_process = st.checkbox("Show step-by-step tool process", value=True)
    
    if st.button("Create Recipe", key="create_recipe"):
        if not inventory_text.strip():
            st.error("Please add some ingredients to your inventory first!")
        else:
            # Clear previous tool outputs
            st.session_state.tool_outputs = []
            
            # Get ingredients list
            ingredients = [ing.strip() for ing in inventory_text.splitlines() if ing.strip()]
            
            # Create the query for the agent with health goals and dietary restrictions
            query = {
                "task": "create_recipe",
                "ingredients": ingredients,
                "preferences": recipe_preferences if recipe_preferences else None,
                "health_goals": {
                    "goal_type": goal_type if goal_type != "None" else None,
                    "restrictions": restrictions if restrictions else None
                }
            }
            
            # Create a container for the tool process
            process_container = st.container()
            
            with process_container:
                if show_tool_process:
                    st.subheader("🔍 Recipe Creation Process")
                    
                    try:
                        with st.spinner("Processing your request..."):
                            # Let the LLM decide tool execution order
                            agent_response = chef_agent(json.dumps(query))
                            
                            # Check if agent_response is a dictionary with the expected structure
                            if isinstance(agent_response, dict) and "reasoning" in agent_response:
                                # Display the agent's reasoning
                                with st.expander("💭 Agent's Reasoning", expanded=True):
                                    st.markdown(agent_response.get("reasoning", "No reasoning provided"))
                                
                                # Execute and display each tool in the sequence
                                for step_index, step in enumerate(agent_response.get("tool_sequence", [])):
                                    tool_name = step.get("tool_name", "Tool")
                                    with st.expander(f"Step {step_index+1}: ✨ {tool_name}", expanded=True):
                                        # Display reason with better formatting
                                        st.markdown(f"### Why this tool?")
                                        st.markdown(f"_{step.get('reason', 'No reason provided')}_")
                                        
                                        # Display input parameters in a clearer format
                                        st.markdown("### Input Parameters")
                                        input_params = step.get("input", {})
                                        if isinstance(input_params, dict):
                                            for param_name, param_value in input_params.items():
                                                if isinstance(param_value, list):
                                                    st.markdown(f"**{param_name}:**")
                                                    for item in param_value:
                                                        st.markdown(f"- {item}")
                                                else:
                                                    st.markdown(f"**{param_name}:** {param_value}")
                                        else:
                                            st.markdown(f"**Input:** {input_params}")
                                        
                                        # Display the output with better formatting
                                        st.markdown("### Output")
                                        output = step.get("output", {})
                                        
                                        # Create columns for a cleaner layout
                                        if tool_name == "recipe_creator":
                                            try:
                                                # If output is a string, try to create a minimal recipe
                                                if isinstance(output, str):
                                                    # Create a minimal recipe from the text output
                                                    recipe_name = "Quick Recipe"
                                                    lines = output.split('\n')
                                                    for line in lines[:3]:  # Check first few lines for a title
                                                        if len(line.strip()) > 0 and len(line.strip()) < 50:
                                                            recipe_name = line.strip()
                                                            break
                                                    
                                                    # Create a minimal recipe
                                                    minimal_recipe = Recipe(
                                                        name=recipe_name,
                                                        ingredients=[Ingredient(name=ing) for ing in ingredients[:5]],
                                                        instructions=["See full recipe details in the output above"]
                                                    )
                                                    st.session_state.recipe_result = minimal_recipe
                                                elif isinstance(output, dict):
                                                    # Display the raw output for debugging
                                                    st.markdown("**Raw Recipe Creator Output:**")
                                                    st.json(output)
                                                    
                                                    # Check if output has a nested 'recipe' object
                                                    if 'recipe' in output and isinstance(output['recipe'], dict):
                                                        recipe_data = output['recipe']
                                                        # Try to parse the nested recipe object
                                                        try:
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
                                                            else:
                                                                recipe_data['ingredients'] = [Ingredient(name=ing) for ing in ingredients]
                                                            
                                                            # Try to extract instructions
                                                            recipe_instructions = []
                                                            if 'instructions' in recipe_data:
                                                                if isinstance(recipe_data['instructions'], list):
                                                                    recipe_instructions = recipe_data['instructions']
                                                                elif isinstance(recipe_data['instructions'], str):
                                                                    recipe_instructions = [line.strip() for line in recipe_data['instructions'].split('\n') if line.strip()]
                                                            
                                                            # If no instructions were found, create a basic one
                                                            if not recipe_instructions:
                                                                recipe_instructions = ["Combine all ingredients", "Cook until done", "Serve and enjoy"]
                                                            
                                                            # Create a recipe with the extracted information
                                                            st.session_state.recipe_result = Recipe(
                                                                name=recipe_data.get('name', f"Recipe with {ingredients[0].capitalize()}"),
                                                                ingredients=[Ingredient(**ing) for ing in recipe_data['ingredients']],
                                                                instructions=recipe_instructions,
                                                                prep_time=recipe_data.get('prep_time'),
                                                                cook_time=recipe_data.get('cook_time'),
                                                                servings=recipe_data.get('servings')
                                                            )
                                                            st.success("Successfully parsed nested recipe data")
                                                        except Exception as nested_error:
                                                            st.warning(f"Could not parse nested recipe: {str(nested_error)}")
                                                            # Create a recipe with the available information
                                                            recipe_name = recipe_data.get('name', f"Recipe with {ingredients[0].capitalize()}")
                                                            
                                                            # Try to extract ingredients
                                                            recipe_ingredients = []
                                                            if 'ingredients' in recipe_data:
                                                                if isinstance(recipe_data['ingredients'], list):
                                                                    for ing in recipe_data['ingredients']:
                                                                        if isinstance(ing, dict) and 'name' in ing:
                                                                            recipe_ingredients.append(Ingredient(**ing))
                                                                        elif isinstance(ing, str):
                                                                            recipe_ingredients.append(Ingredient(name=ing))
                                                            elif isinstance(recipe_data['ingredients'], str):
                                                                for line in recipe_data['ingredients'].split('\n'):
                                                                    if line.strip():
                                                                        recipe_ingredients.append(Ingredient(name=line.strip()))
                                                            
                                                            # If no ingredients were found, use the input ingredients
                                                            if not recipe_ingredients:
                                                                recipe_ingredients = [Ingredient(name=ing) for ing in ingredients]
                                                            
                                                            # Try to extract instructions
                                                            recipe_instructions = []
                                                            if 'instructions' in recipe_data:
                                                                if isinstance(recipe_data['instructions'], list):
                                                                    recipe_instructions = recipe_data['instructions']
                                                                elif isinstance(recipe_data['instructions'], str):
                                                                    recipe_instructions = [line.strip() for line in recipe_data['instructions'].split('\n') if line.strip()]
                                                            
                                                            # If no instructions were found, create a basic one
                                                            if not recipe_instructions:
                                                                recipe_instructions = ["Combine all ingredients", "Cook until done", "Serve and enjoy"]
                                                            
                                                            # Create a recipe with the extracted information
                                                            st.session_state.recipe_result = Recipe(
                                                                name=recipe_name,
                                                                ingredients=recipe_ingredients,
                                                                instructions=recipe_instructions,
                                                                prep_time=recipe_data.get('prep_time'),
                                                                cook_time=recipe_data.get('cook_time'),
                                                                servings=recipe_data.get('servings')
                                                            )
                                                    # Check if output has a 'result' key but not the required Recipe fields
                                                    elif 'result' in output and not all(key in output for key in ['name', 'ingredients', 'instructions']):
                                                        # Create a recipe from the ingredients
                                                        recipe_name = f"Recipe with {ingredients[0].capitalize()}"
                                                        
                                                        # Try to extract a better name from the result if possible
                                                        if isinstance(output['result'], str) and "recipe" in output['result'].lower():
                                                            lines = output['result'].split('\n')
                                                            for line in lines[:3]:
                                                                if len(line.strip()) > 0 and len(line.strip()) < 50 and "recipe" in line.lower():
                                                                    recipe_name = line.strip()
                                                                    break
                                                        
                                                        # Create a minimal recipe
                                                        minimal_recipe = Recipe(
                                                            name=recipe_name,
                                                            ingredients=[Ingredient(name=ing) for ing in ingredients],
                                                            instructions=["See the detailed recipe in the tool output above"]
                                                        )
                                                        
                                                        # If the result is a string, try to parse it for better instructions
                                                        if isinstance(output['result'], str):
                                                            # Look for sections that might be instructions
                                                            sections = output['result'].split('\n\n')
                                                            for section in sections:
                                                                if "instruction" in section.lower() or "step" in section.lower() or section.strip().startswith("1."):
                                                                    minimal_recipe.instructions = [line.strip() for line in section.split('\n') if line.strip()]
                                                        
                                                        st.session_state.recipe_result = minimal_recipe
                                                        
                                                        # Show a warning about the parsing issue
                                                        st.warning("The recipe tool returned a simplified result. Created a basic recipe from available information.")
                                                    else:
                                                        # Try to parse as a Recipe object
                                                        st.session_state.recipe_result = Recipe(**output)
                                            except Exception as e:
                                                st.warning(f"Could not parse recipe: {str(e)}")
                                                st.info("Creating a simplified recipe from the output")
                                                
                                                # Display the raw output for debugging
                                                st.markdown("**Raw Recipe Creator Output:**")
                                                if isinstance(output, dict):
                                                    st.json(output)
                                                else:
                                                    st.markdown(f"```\n{output}\n```")
                                                
                                                # Create a minimal recipe as fallback
                                                st.session_state.recipe_result = Recipe(
                                                    name="Recipe from Ingredients",
                                                    ingredients=[Ingredient(name=ing) for ing in ingredients],
                                                    instructions=["See the detailed recipe in the tool output above"]
                                                )
                                        
                                        elif tool_name == "health_adapter":
                                            try:
                                                if isinstance(output, str):
                                                    # Keep the existing recipe but note the adaptation
                                                    if st.session_state.recipe_result:
                                                        recipe = st.session_state.recipe_result
                                                        recipe.name = f"{recipe.name} (Health Adapted)"
                                                        st.session_state.recipe_result = recipe
                                                elif isinstance(output, dict):
                                                    # Display the raw output for debugging
                                                    st.markdown("**Raw Health Adapter Output:**")
                                                    st.json(output)
                                                    
                                                    # Check if output has a nested 'recipe' object
                                                    if 'recipe' in output and isinstance(output['recipe'], dict):
                                                        recipe_data = output['recipe']
                                                        # Try to parse the nested recipe object
                                                        try:
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
                                                            else:
                                                                recipe_data['ingredients'] = [Ingredient(name=ing) for ing in ingredients]
                                                            
                                                            # Now we can continue with the rest of the code
                                                            recipe_instructions = []
                                                            if 'instructions' in recipe_data:
                                                                if isinstance(recipe_data['instructions'], list):
                                                                    recipe_instructions = recipe_data['instructions']
                                                                elif isinstance(recipe_data['instructions'], str):
                                                                    recipe_instructions = [line.strip() for line in recipe_data['instructions'].split('\n') if line.strip()]
                                                            
                                                            # If no instructions were found, create a basic one
                                                            if not recipe_instructions:
                                                                recipe_instructions = ["Combine all ingredients", "Cook until done", "Serve and enjoy"]
                                                            
                                                            # Create a recipe with the extracted information
                                                            st.session_state.recipe_result = Recipe(
                                                                name=recipe_data.get('name', f"Recipe with {ingredients[0].capitalize()}"),
                                                                ingredients=[Ingredient(**ing) for ing in recipe_data['ingredients']],
                                                                instructions=recipe_instructions,
                                                                prep_time=recipe_data.get('prep_time'),
                                                                cook_time=recipe_data.get('cook_time'),
                                                                servings=recipe_data.get('servings')
                                                            )
                                                            st.success("Successfully parsed nested adapted recipe data")
                                                            # Add adaptation notes if possible
                                                            if 'name' in recipe_data:
                                                                adapted_recipe.instructions.append(f"Health Adaptation: Recipe adapted to '{recipe_data['name']}'")
                                                            st.session_state.recipe_result = adapted_recipe
                                                        except Exception as e:
                                                            st.warning(f"Error formatting ingredients: {str(e)}")
                                                            recipe_data['ingredients'] = [{"name": ing, "quantity": "", "unit": ""} for ing in ingredients]
                                                        
                                                        # Now we can continue with the rest of the code
                                                        recipe_instructions = []
                                                        if 'instructions' in recipe_data:
                                                            if isinstance(recipe_data['instructions'], list):
                                                                recipe_instructions = recipe_data['instructions']
                                                            elif isinstance(recipe_data['instructions'], str):
                                                                recipe_instructions = [line.strip() for line in recipe_data['instructions'].split('\n') if line.strip()]
                                                        
                                                        # If no instructions were found, create a basic one
                                                        if not recipe_instructions:
                                                            recipe_instructions = ["Combine all ingredients", "Cook until done", "Serve and enjoy"]
                                                        
                                                        # Create a recipe with the extracted information
                                                        st.session_state.recipe_result = Recipe(
                                                            name=recipe_data.get('name', f"Recipe with {ingredients[0].capitalize()}"),
                                                            ingredients=[Ingredient(**ing) for ing in recipe_data['ingredients']],
                                                            instructions=recipe_instructions,
                                                            prep_time=recipe_data.get('prep_time'),
                                                            cook_time=recipe_data.get('cook_time'),
                                                            servings=recipe_data.get('servings')
                                                        )
                                                        st.success("Successfully parsed nested adapted recipe data")
                                                        # Add adaptation notes if possible
                                                        if 'name' in recipe_data:
                                                            adapted_recipe.instructions.append(f"Health Adaptation: Recipe adapted to '{recipe_data['name']}'")
                                                        st.session_state.recipe_result = adapted_recipe
                                                    elif 'result' in output and not all(key in output for key in ['name', 'ingredients', 'instructions']):
                                                        # Keep the existing recipe but add the adaptation notes
                                                        if st.session_state.recipe_result:
                                                            recipe = st.session_state.recipe_result
                                                            recipe.name = f"{recipe.name} (Health Adapted)"
                                                            # Add adaptation notes to instructions
                                                            if isinstance(output['result'], str):
                                                                recipe.instructions.append(f"Health Adaptation: {output['result']}")
                                                            st.session_state.recipe_result = recipe
                                                else:
                                                    # Try to parse as a Recipe object
                                                    adapted_recipe = Recipe(**output)
                                                    st.session_state.health_adapted_recipe = adapted_recipe
                                                    st.session_state.recipe_result = adapted_recipe
                                            except Exception as e:
                                                st.warning(f"Could not parse adapted recipe: {str(e)}")
                                                # Display the raw output for debugging
                                                st.markdown("**Raw Health Adapter Output:**")
                                                if isinstance(output, dict):
                                                    st.json(output)
                                                else:
                                                    st.markdown(f"```\n{output}\n```")
                                                
                                                # Keep the existing recipe but note the adaptation attempt
                                                if st.session_state.recipe_result:
                                                    recipe = st.session_state.recipe_result
                                                    recipe.name = f"{recipe.name} (Health Adapted - parsing failed)"
                                                    st.session_state.recipe_result = recipe
                                        
                                        else:
                                            # For other tools, display the output as is
                                            if isinstance(output, dict):
                                                st.json(output)
                                            elif isinstance(output, str):
                                                st.markdown(output)
                                            else:
                                                st.write(output)
                                        
                                        # Add a divider between input/output and the tool processing logic
                                        st.markdown("---")
                                        st.markdown("### Tool Processing")
                                        
                                        # Store tool output in session state
                                        st.session_state.tool_outputs.append({
                                            "tool": tool_name,
                                            "input": input_params,
                                            "output": output
                                        })
                                
                                # Check if a recipe was created, if not, create one directly
                                if not st.session_state.recipe_result:
                                    st.warning("No recipe was created by the tools. Creating a recipe directly...")
                                    try:
                                        # Create a recipe directly using the recipe_creator tool
                                        direct_recipe = recipe_creator(ingredients, {"description": recipe_preferences} if recipe_preferences else None)
                                        st.session_state.recipe_result = direct_recipe
                                        st.success("Recipe created directly!")
                                    except Exception as e:
                                        st.error(f"Error creating recipe directly: {str(e)}")
                                        # Create a minimal recipe as last resort
                                        st.session_state.recipe_result = Recipe(
                                            name=f"Simple {ingredients[0].capitalize()} Recipe",
                                            ingredients=[Ingredient(name=ing) for ing in ingredients],
                                            instructions=["Combine all ingredients", "Cook until done", "Serve and enjoy"]
                                        )
                                
                                st.success("🎉 Recipe creation process complete!")
                    except Exception as e:
                        st.error(f"Error processing request: {str(e)}")
                        st.info("Falling back to the general chef agent...")
                        fallback_query = f"Create a recipe using these ingredients: {', '.join(ingredients)}."
                        if recipe_preferences:
                            fallback_query += f" Preferences: {recipe_preferences}."
                        if use_health_goals and goal_type != "None":
                            fallback_query += f" Health goal: {goal_type}."
                            if restrictions:
                                fallback_query += f" Dietary restrictions: {', '.join(restrictions)}."
                        
                        try:
                            result = chef_agent(fallback_query)
                            if isinstance(result, dict) and "final_result" in result:
                                st.markdown(result["final_result"])
                            else:
                                st.markdown(str(result))
                        except Exception as fallback_error:
                            st.error(f"Fallback also failed: {str(fallback_error)}")
                            st.markdown("Please try again with different ingredients or preferences.")
    
    # Display final recipe if available
    if st.session_state.recipe_result:
        st.markdown("---")
        
        # Create a nice card-like container for the recipe
        recipe_container = st.container()
        with recipe_container:
            # Add some styling
            st.markdown("""
            <style>
            .recipe-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .recipe-title {
                color: #4b6584;
                text-align: center;
                margin-bottom: 20px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Start the recipe card
            st.markdown("<div class='recipe-card'>", unsafe_allow_html=True)
            st.markdown("<div class='recipe-title'>📝 Your Final Recipe</div>", unsafe_allow_html=True)
            
            st.subheader(st.session_state.recipe_result.name)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Preparation Time:**", f"{st.session_state.recipe_result.prep_time} minutes" if st.session_state.recipe_result.prep_time else "Not specified")
            with col2:
                st.write("**Cooking Time:**", f"{st.session_state.recipe_result.cook_time} minutes" if st.session_state.recipe_result.cook_time else "Not specified")
            with col3:
                st.write("**Servings:**", st.session_state.recipe_result.servings or "Not specified")
            
            st.subheader("Ingredients")
            for ing in st.session_state.recipe_result.ingredients:
                if isinstance(ing, dict):
                    quantity = ing.get('quantity', '')
                    unit = ing.get('unit', '')
                    name = ing.get('name', '')
                    st.write(f"- {quantity} {unit} {name}")
                else:
                    quantity = getattr(ing, 'quantity', '') or ''
                    unit = getattr(ing, 'unit', '') or ''
                    name = getattr(ing, 'name', str(ing))
                    st.write(f"- {quantity} {unit} {name}")
            
            st.subheader("Instructions")
            for i, step in enumerate(st.session_state.recipe_result.instructions):
                st.write(f"{i+1}. {step}")
            
            # Add a section to display the raw recipe data for debugging
            with st.expander("Debug: Raw Recipe Data"):
                st.json(st.session_state.recipe_result.__dict__)
            
            if st.session_state.recipe_result.nutrition:
                st.subheader("Nutrition Information")
                
                # Display key nutrition facts in a more readable format
                if isinstance(st.session_state.recipe_result.nutrition, dict):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Calories:**", st.session_state.recipe_result.nutrition.get("calories", "Not available"))
                        st.write("**Protein:**", st.session_state.recipe_result.nutrition.get("protein", "Not available"))
                        st.write("**Carbs:**", st.session_state.recipe_result.nutrition.get("carbs", "Not available"))
                    
                    with col2:
                        st.write("**Fat:**", st.session_state.recipe_result.nutrition.get("fat", "Not available"))
                        st.write("**Fiber:**", st.session_state.recipe_result.nutrition.get("fiber", "Not available"))
                        st.write("**Sugar:**", st.session_state.recipe_result.nutrition.get("sugar", "Not available"))
                    
                    # Show full nutrition details in an expander
                    with st.expander("View Full Nutrition Details"):
                        st.json(st.session_state.recipe_result.nutrition)
                else:
                    st.json(st.session_state.recipe_result.nutrition)
            
            # Add a button to prepare the dish
            if st.button("Prepare This Dish"):
                with st.spinner("Creating detailed preparation guide..."):
                    try:
                        # Get health goals if specified
                        health_goal = None
                        if use_health_goals and goal_type != "None":
                            health_goal = goal_type
                        
                        # Call the dish preparer tool
                        preparation_result = dish_preparer(
                            st.session_state.recipe_result,
                            health_goal,
                            restrictions if restrictions else None
                        )
                        
                        # Store the result
                        st.session_state.preparation_guide = preparation_result
                        st.success("Preparation guide created!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error creating preparation guide: {str(e)}")
            
            # Display preparation guide if available
            if st.session_state.preparation_guide:
                st.markdown("</div>", unsafe_allow_html=True)  # Close the recipe card
                
                # Create a new card for the preparation guide
                st.markdown("<div class='recipe-card'>", unsafe_allow_html=True)
                
                # Display the technique name prominently
                prep_guide = st.session_state.preparation_guide
                technique_name = prep_guide.get('technique_name', "Chef's Preparation Guide")
                
                st.markdown(f"<div class='recipe-title'>👨‍🍳 {technique_name}</div>", unsafe_allow_html=True)
                
                # Display recipe name
                st.markdown(f"### For: {prep_guide['recipe_name']}")
                
                # Display health considerations if any
                if prep_guide['health_considerations']:
                    st.markdown(f"**Health Focus:** {prep_guide['health_considerations']}")
                
                # Display dietary restrictions if any
                if prep_guide['dietary_restrictions']:
                    st.markdown(f"**Dietary Restrictions:** {', '.join(prep_guide['dietary_restrictions'])}")
                
                # Create tabs for different sections of the preparation guide
                prep_tabs = st.tabs(["Full Guide", "Preparation Steps", "Cooking Tips", "Presentation"])
                
                with prep_tabs[0]:
                    # Display the full preparation guide with markdown formatting
                    st.markdown(prep_guide['preparation_guide'])
                
                with prep_tabs[1]:
                    # Try to extract preparation steps section
                    guide_text = prep_guide['preparation_guide']
                    if "Preparation" in guide_text or "Steps" in guide_text:
                        sections = guide_text.split("##")
                        for section in sections:
                            if "Preparation" in section or "Steps" in section or "Instructions" in section:
                                st.markdown(f"## {section}")
                                break
                    else:
                        st.markdown("See the Full Guide tab for preparation steps.")
                
                with prep_tabs[2]:
                    # Try to extract cooking tips section
                    guide_text = prep_guide['preparation_guide']
                    if "Tips" in guide_text or "Techniques" in guide_text:
                        sections = guide_text.split("##")
                        for section in sections:
                            if "Tips" in section or "Techniques" in section:
                                st.markdown(f"## {section}")
                                break
                    else:
                        st.markdown("See the Full Guide tab for cooking tips.")
                
                with prep_tabs[3]:
                    # Try to extract presentation section
                    guide_text = prep_guide['preparation_guide']
                    if "Presentation" in guide_text or "Plating" in guide_text or "Serving" in guide_text:
                        sections = guide_text.split("##")
                        for section in sections:
                            if "Presentation" in section or "Plating" in section or "Serving" in section:
                                st.markdown(f"## {section}")
                                break
                    else:
                        st.markdown("See the Full Guide tab for presentation suggestions.")
                
                # Button to clear the preparation guide
                if st.button("Clear Preparation Guide"):
                    st.session_state.preparation_guide = None
                    st.experimental_rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("</div>", unsafe_allow_html=True)  # Close the recipe card

with tab2:
    st.header("Create a Meal Plan")
    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input("Number of days:", min_value=1, max_value=7, value=3)
    with col2:
        meals_per_day = st.number_input("Meals per day:", min_value=1, max_value=6, value=3)
    
    meal_plan_notes = st.text_area(
        "Any specific notes for your meal plan?",
        placeholder="I prefer simple breakfasts and more elaborate dinners"
    )
    
    if st.button("Create Meal Plan", key="create_meal_plan"):
        if not inventory_text.strip():
            st.error("Please add some ingredients to your inventory first!")
        else:
            with st.spinner("Creating your meal plan..."):
                ingredients = [ing.strip() for ing in inventory_text.splitlines() if ing.strip()]
                
                try:
                    # First analyze the inventory
                    inventory_analysis = inventory_analyzer(ingredients)
                    st.success("✅ Inventory analyzed")
                    
                    # Create health goal if needed
                    health_goal = None
                    if use_health_goals and goal_type != "None":
                        health_goal = HealthGoal(
                            goal_type=goal_type,
                            restrictions=restrictions if restrictions else None
                        )
                    
                    # Create the meal plan
                    try:
                        meal_plan = meal_planner(ingredients, days, meals_per_day, health_goal)
                        # Store the result and display success
                        st.session_state.meal_plan_result = meal_plan
                        st.success("✅ Meal plan created successfully!")
                    except Exception as meal_plan_error:
                        st.warning(f"Error in meal planner: {str(meal_plan_error)}")
                        st.info("Creating a simplified meal plan...")
                        
                        # Create a simplified meal plan as fallback
                        simplified_recipes = []
                        for day in range(1, days + 1):
                            for meal in range(1, meals_per_day + 1):
                                meal_type = ["Breakfast", "Lunch", "Dinner"][meal % 3]
                                simplified_recipes.append({
                                    "day": day,
                                    "meal_type": meal_type,
                                    "name": f"Simple {meal_type} with {', '.join(ingredients[:3])}",
                                    "description": "A simple meal using available ingredients",
                                    "main_ingredients": ingredients[:5],
                                    "nutrition": "Not available"
                                })
                        
                        from recipe_agent import MealPlan
                        simplified_meal_plan = MealPlan(
                            days=days,
                            meals_per_day=meals_per_day,
                            recipes=simplified_recipes,
                            nutrition_summary={"note": "Simplified meal plan - detailed nutrition not available"}
                        )
                        st.session_state.meal_plan_result = simplified_meal_plan
                        st.success("✅ Simplified meal plan created")
                        
                except Exception as e:
                    st.error(f"Error creating meal plan: {str(e)}")
                    st.info("Falling back to the general chef agent...")
                    
                    # Fallback to the general agent
                    query = f"Create a {days}-day meal plan with {meals_per_day} meals per day using these ingredients: {', '.join(ingredients)}."
                    if meal_plan_notes:
                        query += f" Notes: {meal_plan_notes}."
                    if use_health_goals:
                        query += f" Health goal: {goal_type}."
                        if restrictions:
                            query += f" Dietary restrictions: {', '.join(restrictions)}."
                    
                    result = chef_agent(query)
                    if isinstance(result, dict) and "final_result" in result:
                        st.session_state.meal_plan_result = result["final_result"]
                    else:
                        st.session_state.meal_plan_result = str(result)
    
    # Display meal plan if available
    if st.session_state.meal_plan_result:
        st.markdown("---")
        st.header("📅 Your Meal Plan")
        
        if isinstance(st.session_state.meal_plan_result, str):
            # If it's a string (from the fallback), just display it
            st.markdown(st.session_state.meal_plan_result)
        else:
            # If it's a MealPlan object, format it nicely
            meal_plan = st.session_state.meal_plan_result
            
            st.write(f"**{meal_plan.days}-Day Meal Plan with {meal_plan.meals_per_day} meals per day**")
            
            # Display each day's meals
            for day_idx in range(meal_plan.days):
                st.subheader(f"Day {day_idx + 1}")
                
                # Get meals for this day
                day_meals = [meal for meal in meal_plan.recipes 
                            if meal.get("day", 0) == day_idx + 1 or 
                               meal.get("day_index", 0) == day_idx]
                
                if not day_meals:
                    # If day information is not available, divide recipes evenly
                    start_idx = day_idx * meal_plan.meals_per_day
                    end_idx = start_idx + meal_plan.meals_per_day
                    day_meals = meal_plan.recipes[start_idx:end_idx]
                
                # Display each meal
                for meal_idx, meal in enumerate(day_meals[:meal_plan.meals_per_day]):
                    meal_name = meal.get("name", f"Meal {meal_idx + 1}")
                    meal_type = meal.get("meal_type", ["Breakfast", "Lunch", "Dinner"][meal_idx % 3])
                    
                    with st.expander(f"{meal_type}: {meal_name}", expanded=True):
                        st.write("**Description:**", meal.get("description", "No description available"))
                        
                        st.write("**Main Ingredients:**")
                        ingredients = meal.get("ingredients", meal.get("main_ingredients", []))
                        if isinstance(ingredients, list):
                            for ing in ingredients:
                                if isinstance(ing, dict):
                                    st.write(f"- {ing.get('quantity', '')} {ing.get('unit', '')} {ing.get('name', '')}")
                                else:
                                    st.write(f"- {ing}")
                        else:
                            st.write(ingredients)
                        
                        if "nutrition" in meal:
                            st.write("**Nutrition:**", meal["nutrition"])
            
            # Display nutrition summary if available
            if meal_plan.nutrition_summary:
                st.subheader("Nutrition Summary")
                st.json(meal_plan.nutrition_summary)
        
        # Button to clear the meal plan
        if st.button("Clear Meal Plan"):
            st.session_state.meal_plan_result = None
            st.experimental_rerun()

with tab3:
    st.header("Analyze Recipe Nutrition")
    recipe_to_analyze = st.text_area(
        "Paste a recipe to analyze its nutritional content:",
        height=300,
        placeholder="Recipe Name: Chicken Stir-Fry\n\nIngredients:\n- 2 chicken breasts\n- 1 cup rice\n- 1 bell pepper\n...\n\nInstructions:\n1. Cook rice according to package instructions\n2. Slice chicken and vegetables\n..."
    )
    
    if st.button("Analyze Nutrition", key="analyze_nutrition"):
        if not recipe_to_analyze.strip():
            st.error("Please paste a recipe to analyze!")
        else:
            with st.spinner("Analyzing recipe nutrition..."):
                query = f"Analyze the nutritional content of this recipe:\n\n{recipe_to_analyze}"
                if use_health_goals:
                    query += f"\n\nAlso, evaluate if this recipe is suitable for {goal_type} goal"
                    if restrictions:
                        query += f" with {', '.join(restrictions)} restrictions"
                    query += "."
                
                result = chef_agent(query)
                if isinstance(result, dict) and "final_result" in result:
                    st.session_state.nutrition_result = result["final_result"]
                else:
                    st.session_state.nutrition_result = str(result)
    
    # Display nutrition analysis if available
    if st.session_state.nutrition_result:
        st.markdown("---")
        st.header("🔬 Nutrition Analysis")
        st.markdown(st.session_state.nutrition_result)
        
        # Button to clear the nutrition analysis
        if st.button("Clear Nutrition Analysis"):
            st.session_state.nutrition_result = None
            st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("ChefGPT uses AI to help you cook smarter with what you have. Developed with ❤️ using OpenAI's GPT models.") 
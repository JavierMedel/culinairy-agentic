from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi import HTTPException
from utils.loader import load_recipes_from_file, get_recipe_by_id, attach_recipe_images
import random

app = FastAPI(
    title="CulinAIry Agentic API",
    description="""
🍳 **CulinAIry Agentic API**

Plan optimized meals, explore AI-curated recipes, and integrate LLM-powered meal planning.  
Built for the **AWS + NVIDIA Agentic AI Hackathon**.
""",
    version="1.0.0",
)

# Load all recipes from single JSON file
RECIPES = load_recipes_from_file("recipes_updated.json")

class MealRequest(BaseModel):
    meals_per_day: int
    days: int
    preferences: List[str] = []  # e.g., ["low carb", "chicken", "italian"]

@app.get("/", tags=["Root"])
def home():
    return {"message": "Welcome to the CulinAIry Agentic API!"}

class MealPlan(BaseModel):
    day: int
    meals: List[Dict[str, Any]]
    
@app.post(
    "/plan-meals",
    tags=["Meal Planner"],
    summary="Generate a meal plan",
    description="""
    🧠 Generate a meal plan using available recipes.  
    Filters recipes by preferences (optional), then organizes them by day and meal.
    
    Example:
    ```json
    {
      "meals_per_day": 2,
      "days": 3,
      "preferences": ["low carb", "mexican"]
    }
    ```
    """,
    response_model=Dict[str, Any]
)
def plan_meals(request: MealRequest):
    # Filter recipes by preferences if provided
    filtered_recipes = RECIPES

    if request.preferences:
        preferences_lower = [p.lower() for p in request.preferences]
        filtered_recipes = [
            r for r in RECIPES
            if any(pref in r["title"].lower() or pref in r.get("cousine", "").lower() for pref in preferences_lower)
        ]

    if not filtered_recipes:
        return {"error": "No recipes match your preferences."}

    total_needed = request.meals_per_day * request.days
    if len(filtered_recipes) < total_needed:
        print(f"⚠️ Not enough recipes to fill all slots — reusing some recipes.")
    
    # Randomly select recipes
    selected_recipes = random.choices(filtered_recipes, k=total_needed)

    # Attach all images to each recipe (dish, steps, ingredients)
    selected_recipes_with_images = [attach_recipe_images(r) for r in selected_recipes]

    # Structure the plan by day
    plan = []
    for day in range(1, request.days + 1):
        start_idx = (day - 1) * request.meals_per_day
        end_idx = start_idx + request.meals_per_day
        plan.append({
            "day": day,
            "meals": selected_recipes_with_images[start_idx:end_idx]
        })

    return {
        "summary": {
            "days": request.days,
            "meals_per_day": request.meals_per_day,
            "preferences": request.preferences,
            "total_recipes": len(filtered_recipes)
        },
        "plan": plan
    }

@app.get("/recipes", tags=["Recipes"])
def list_recipes(limit: int = 10):
    """
    List recipes. Optional query parameter 'limit' to control number of recipes returned.
    Return a list of recipes with images attached.
    Example: /recipes?limit=5
    """
    return [attach_recipe_images(r) for r in RECIPES[:limit]]

@app.get("/recipe/{recipe_id}", tags=["Recipes"])
def read_recipe(recipe_id: str):
    """
    Fetch a single recipe by ID with images attached.
    Example: /recipe/cal-smart-tex-mex-beef-bowls
    """
    # Get the recipe
    recipe = get_recipe_by_id(RECIPES, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Attach images (dish, steps, ingredients)
    recipe_with_images = attach_recipe_images(recipe)
    
    return recipe_with_images


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

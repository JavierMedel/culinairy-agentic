from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from utils.loader import load_recipes_from_file
import random

app = FastAPI(title="CulinAIry Agentic API")

# Load all recipes from single JSON file
RECIPES = load_recipes_from_file("recipes_updated.json")

class MealRequest(BaseModel):
    meals_per_day: int
    days: int
    preferences: List[str] = []  # e.g., ["low carb", "chicken", "italian"]

class MealPlan(BaseModel):
    day: int
    meals: List[Dict[str, Any]]

@app.post("/plan-meals")
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
    
    selected_recipes = random.choices(filtered_recipes, k=total_needed)

    # Structure the plan by day
    plan = []
    for day in range(1, request.days + 1):
        start_idx = (day - 1) * request.meals_per_day
        end_idx = start_idx + request.meals_per_day
        plan.append({
            "day": day,
            "meals": selected_recipes[start_idx:end_idx]
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

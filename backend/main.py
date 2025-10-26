from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from fastapi import HTTPException
from utils.loader import load_recipes_from_file, get_recipe_by_id, attach_recipe_images
from utils.embeddings_helper import add_recipe_embedding, find_similar_recipes
from utils.ai_agent import query_nim
from dotenv import load_dotenv

import random
import json
import os

load_dotenv()
NIM_KEY = os.getenv("NIM_KEY")


tags_metadata = [
    {
        "name": "Root",
        "description": "Check server status and base API message."
    },
    {
        "name": "Meal Planner",
        "description": "Generate optimized AI meal plans using recipe data and filters."
    },
    {
        "name": "Recipes",
        "description": "Access recipes, details, and images."
    },
]

app = FastAPI(
    title="CulinAIry Agentic API",
    description="""
🍳 **CulinAIry Agentic API**

Plan optimized meals, explore AI-curated recipes, and integrate LLM-powered meal planning.  
Built for the **AWS + NVIDIA Agentic AI Hackathon**.
""",
    version="1.0.1",
    openapi_tags=tags_metadata,
    contact={
        "name": "CulinAIry Team",
        "url": "https://github.com/JavierMedel/culinairy-agentic",
        "email": "javier.medel@culinairy.world",
    }
)

from fastapi.staticfiles import StaticFiles
import os
# --- Serve Static Files (Images) ---
# Mounts /images so they can be accessed at http://localhost:8000/images/...
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
if os.path.exists(IMAGE_DIR):
    app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")
else:
    print("⚠️ Warning: 'images' folder not found — static serving disabled.")

# ------------------------------------------------------
# 🌐 CORS Settings
# ------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------
# 📦 Data Load
# ------------------------------------------------------
RECIPES = load_recipes_from_file("recipes_updated.json")


print("⚡ Generating embeddings for recipes... (this may take a few minutes)")
for r in RECIPES:
    add_recipe_embedding(r["id_legacy"], r["title"] + " " + r.get("description", ""))

print("✅ Recipe embeddings ready!")
print(find_similar_recipes("Low-carb Italian chicken dinner"))


class MealRequest(BaseModel):
    meals_per_day: int = Field(..., gt=0, le=5, description="Number of meals per day")
    days: int = Field(..., gt=0, le=7, description="Number of days to plan meals for")
    preferences: List[str] = Field(default_factory=list, description="List of user preferences or dietary tags") # e.g., ["low carb", "chicken", "italian"]

@app.get("/", tags=["Root"])
def home():
    """
    🌐 Root endpoint — confirms the API is running.
    """
    return {"message": "Welcome to the CulinAIry Agentic API! Visit /docs for API documentation."}

@app.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}

# ------------------------------------------------------
# 🧠 Meal Planning
# ------------------------------------------------------

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
    response_model=Dict[str, Any],
     responses={
        200: {
            "description": "Meal plan successfully generated",
            "content": {
                "application/json": {
                    "example": {
                        "summary": {
                            "days": 3,
                            "meals_per_day": 2,
                            "preferences": ["low carb", "mexican"],
                            "total_recipes": 18
                        },
                        "plan": [
                            {
                                "day": 1,
                                "meals": [
                                    {"title": "Low-Carb Tex-Mex Beef Bowl", "cousine": "Tex-Mex"},
                                    {"title": "Chicken Caesar Salad", "cousine": "American"}
                                ]
                            }
                        ]
                    }
                }
            },
        }
    },
)

@app.post("/plan-meals", tags=["Meal Planner"])
def plan_meals(request: MealRequest):
    """
    Generate a meal plan using available recipes.
    Filters recipes by preferences (optional), then organizes them by day and meal.
    Uses NVIDIA NIM AI for reasoning-based selection with fallback to random selection.
    """

    # -----------------------
    # Step 1: Filter recipes based on preferences
    # -----------------------
    filtered_recipes = RECIPES
    if request.preferences:
        prefs = [p.lower() for p in request.preferences]
        filtered_recipes = [
            r for r in RECIPES
            if any(pref in r["title"].lower() or pref in r.get("cousine", "").lower() for pref in prefs)
        ]

    if not filtered_recipes:
        raise HTTPException(status_code=404, detail="No recipes match your preferences")

    total_needed = request.meals_per_day * request.days

    print(f"Filtered to {filtered_recipes} recipes based on preferences.")

    # -----------------------
    # Step 2: Build AI prompt for meal planning
    # -----------------------
    prompt = f"""
    You are an AI meal planner for CulinAIry.
    You have access to {len(filtered_recipes)} recipes.
    Each recipe includes title, cuisine, and nutritional info.

    User request:
    - {request.meals_per_day} meals per day
    - for {request.days} days
    - preferences: {', '.join(request.preferences) if request.preferences else 'none'}
    - recipes {filtered_recipes}

    Select recipes that fit the user's preferences, ensuring variety and balance.
    Return a JSON list of recipe IDs (id_legacy) only.
    """

    print("AI Meal Plan Prompt:", prompt)

    # -----------------------
    # Step 3: Query NIM for reasoning-based selection
    # -----------------------
    try:
        ai_response = query_nim(prompt)
        selected_ids = json.loads(ai_response)
    except json.JSONDecodeError:
        print("⚠️ AI response invalid, falling back to random selection")
        import random
        selected_ids = [r["id_legacy"] for r in random.choices(filtered_recipes, k=total_needed)]

    print("Selected recipe IDs:", selected_ids)

    # -----------------------
    # Step 4: Match recipes by ID
    # -----------------------
    selected_recipes = [r for r in filtered_recipes if r.get("id_legacy") in selected_ids]
    if len(selected_recipes) < total_needed:
        import random
        selected_recipes += random.choices(filtered_recipes, k=total_needed - len(selected_recipes))

    # -----------------------
    # Step 5: Attach images
    # -----------------------
    selected_recipes_with_images = [attach_recipe_images(r) for r in selected_recipes]

    # -----------------------
    # Step 6: Structure plan by day
    # -----------------------
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

# ------------------------------------------------------
# 📖 Recipes Endpoints
# ------------------------------------------------------
# -------------------------------
# List all recipes with optional limit
# -------------------------------

@app.get("/recipes", tags=["Recipes"])
def list_recipes(limit: int = 10):
    """
    List recipes. Optional query parameter 'limit' to control number of recipes returned.
    Return a list of recipes with images attached.
    Example: /recipes?limit=5
    """
    return [attach_recipe_images(r) for r in RECIPES[:limit]]

# -------------------------------
# Fetch a single recipe by ID
# -------------------------------
@app.get("/recipe/{recipe_id}", tags=["Recipes"])
def read_recipe(recipe_id: str):
    """
    Fetch a single recipe by ID with images attached.
    Uses NIM to recommend similar recipes intelligently.
    Example: /recipe/cal-smart-tex-mex-beef-bowls
    """
    # Step 1: Find the recipe
    recipe = get_recipe_by_id(RECIPES, recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Step 2: Attach all images
    recipe_with_images = attach_recipe_images(recipe)

    # Step 3: get AI-recommended similar recipes
    similar_recipes = []
    try:
        prompt = f"""
        You are an AI recipe recommender for CulinAIry.
        Given the following recipe:
        - Title: {recipe['title']}
        - Cuisine: {recipe.get('cousine', 'unknown')}
        - Description: {recipe.get('description', 'no description')}
        
        Recommend 3 similar recipes from the available list based on ingredients, cuisine, or flavor profile.
        Return only a JSON list of recipe IDs (id_legacy).
        """
        ai_response = query_nim(prompt)
        similar_ids = json.loads(ai_response)
        similar_recipes = [
            attach_recipe_images(r) for r in RECIPES if r.get("id_legacy") in similar_ids
        ]
    except Exception as e:
        print("⚠️ AI recommendations failed, using embeddings. Error:", e)
        # fallback to embedding similarity
        similar_ids = find_similar_recipes(recipe_id, top_k=3)
        similar_recipes = [attach_recipe_images(r) for r in RECIPES if r.get("id_legacy") in similar_ids]

    recipe_with_images["recommended_recipes"] = similar_recipes
    return recipe_with_images



# -------------------
# AI test endpoint
# -------------------
@app.get("/ai/test", tags=["AI"])
def ai_test():
    from utils.ai_agent import query_nim
    prompt = "Give me 5 dinner ideas that are low-carb and Mexican inspired."
    response = query_nim(prompt)
    return {"prompt": prompt, "response": response}


# ------------------------------------------------------
# 🚀 Run Server
# ------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)  # or any other port

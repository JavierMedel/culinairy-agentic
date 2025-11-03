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
# print(find_similar_recipes("Low-carb Italian chicken dinner"))

class MealRequest(BaseModel):
    meals_per_day: int = Field(..., gt=0, le=5, description="Number of meals per day")
    days: int = Field(..., gt=0, le=7, description="Number of days to plan meals for")
    preferences: List[str] = Field(default_factory=list, description="List of user preferences or dietary tags") # e.g., ["low carb", "chicken", "italian"]

class RecipeSearchRequest(BaseModel):
    query: str = Field(..., description="User search query for recipes")
    top_k: int = Field(3, gt=0, le=10, description="Number of top recipes to return")


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


@app.post("/search-recipes", tags=["Recipes Agentic Search"])
def search_recipes(request: RecipeSearchRequest):
    """
    Search recipes using embeddings + LLM reasoning (RAG pattern).
    Steps:
      1. Convert user query to embedding.
      2. Retrieve top similar recipes from vector DB.
      3. Use these recipes as context for LLM.
      4. Ask LLM to select best matching recipes.
      5. Return a list of recipe IDs.
    """
    # -----------------------
    # Step 1: Build semantic query
    # -----------------------
    user_query = request.query.strip() if request.query else "balanced meals"
    print(f"🔍 User query: {user_query}")

    # -----------------------
    # Step 2: Retrieve top similar recipes from vector DB
    # -----------------------
    try:
        similar_recipes = find_similar_recipes(user_query, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")

    if not similar_recipes:
        raise HTTPException(status_code=404, detail="No recipes found for this query")

    print(f"✅ Retrieved {len(similar_recipes)} semantically similar recipes")

    # -----------------------
    # Step 3: Prepare detailed recipe context for LLM
    # -----------------------
    recipe_context = []
    for r in similar_recipes:
        full_recipe = get_recipe_by_id(RECIPES, r)
        if full_recipe:
            recipe_context.append({
                "id": full_recipe.get("id_legacy") or full_recipe.get("id"),
                "title": full_recipe.get("title"),
                "description": full_recipe.get("description", ""),
                "ingredients": [ing.get("name") for ing in full_recipe.get("ingredients", [])],
                "utensils": full_recipe.get("utensils", []),
                "tags": full_recipe.get("tags", []),
            })

    print(f"🧩 Prepared recipe context for {len(recipe_context)} recipes")

    # -----------------------
    # Step 4: Build LLM prompt
    # -----------------------
    prompt = f"""
    You are an AI recipe assistant for CulinAIry.

    The user wants recipes for the following query:
    "{user_query}"

    You have access to {len(recipe_context)} relevant recipes:
    {json.dumps(recipe_context, indent=2)}

    Select up to {request.top_k} recipes that best match the user's query.
    Return ONLY a JSON list of recipe IDs ("id") in selection order.
    """

    print("🧠 Sending prompt to LLM...")

    # -----------------------
    # Step 5: Query LLM
    # -----------------------
    try:
        ai_response = query_nim(prompt)
        selected_ids = json.loads(ai_response)
    except Exception as e:
        print("⚠️ LLM response invalid, using fallback random selection.", e)
        import random
        selected_ids = [
            get_recipe_by_id(RECIPES, r).get("id_legacy") or get_recipe_by_id(RECIPES, r).get("id")
            for r in random.choices(similar_recipes, k=request.top_k)
        ]

    print(f"✅ Selected recipe IDs: {selected_ids}")

    # -----------------------
    # Step 6: Return recipe IDs only
    # -----------------------
    return {
        "query": user_query,
        "count": len(selected_ids),
        "recipe_ids": selected_ids
    }

@app.post("/plan-meals", tags=["Meal Planner"])
def plan_meals(request: MealRequest):
    """
    Generate a meal plan using embeddings + LLM reasoning (RAG pattern).
    Steps:
      1. Build semantic query from user preferences.
      2. Retrieve top similar recipes from the vector DB.
      3. Use these recipes as context for the LLM.
      4. Prepare detailed recipe context.
      5. Send structured prompt to NIM (LLM).
      6. Parse LLM response (selected recipe IDs).
      7. Match recipes by ID and prepare full recipe objects.
      8. Attach images.
      9. Structure plan by day.
     10. Return final JSON response.
    """

    # -----------------------
    # Step 1: Build semantic query
    # -----------------------
    user_query = ", ".join(request.preferences) if request.preferences else "balanced weekly meals"
    print(f"🔍 User query: {user_query}")

    # -----------------------
    # Step 2: Retrieve top similar recipes from vector DB
    # -----------------------
    try:
        similar_recipes = find_similar_recipes(user_query, top_k=5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")

    if not similar_recipes:
        raise HTTPException(status_code=404, detail="No similar recipes found")

    print(f"✅ Retrieved {len(similar_recipes)} semantically similar recipes: {similar_recipes}")

    # -----------------------
    # Step 4: Prepare detailed recipe context
    # -----------------------
    recipe_context = []
    for r in similar_recipes:
        # Reuse helper function to get full recipe info
        full_recipe = get_recipe_by_id(RECIPES, r)
        if full_recipe:
            context_entry = {
                "id": full_recipe.get("id_legacy") or full_recipe.get("id"),
                "title": full_recipe.get("title"),
                "description": full_recipe.get("description", ""),
                "ingredients": [ing.get("name") for ing in full_recipe.get("ingredients", [])],
                "utensils": full_recipe.get("utensils", []),
                "tags": full_recipe.get("tags", []),
            }
            recipe_context.append(context_entry)

    print(f"🧩 Assembled recipe context for {len(recipe_context)} recipes")

    # -----------------------
    # Step 5: Build AI prompt with detailed context
    # -----------------------
    prompt = f"""
    You are an AI meal planner for CulinAIry.

    The user wants:
    - {request.meals_per_day} meals per day
    - for {request.days} days
    - preferences: {user_query}

    You have access to {len(recipe_context)} semantically relevant recipes:
    {json.dumps(recipe_context, indent=2)}

    Select recipes that fit the user's preferences, ensuring variety, balance, and no repetition.
    Return ONLY a JSON list of recipe IDs ("id") in selection order.
    """

    print("🧠 Sending prompt to NIM...")

    # -----------------------
    # Step 6: Query LLM (NIM)
    # -----------------------
    try:
        ai_response = query_nim(prompt)
        selected_ids = json.loads(ai_response)
    except Exception as e:
        print("⚠️ AI response invalid, using fallback random selection.", e)
        import random
        selected_ids = random.choices(similar_recipes, k=request.meals_per_day * request.days)

    print("Selected recipe IDs:", selected_ids)

    # -----------------------
    # ✅ Step 7 – Match recipes by ID (reuse Step 4 logic)
    # -----------------------
    selected_recipes = []
    for recipe_id in selected_ids:
        # Reuse get_recipe_by_id to locate recipes
        recipe_data = get_recipe_by_id(RECIPES, recipe_id)
        if recipe_data:
            selected_recipes.append(recipe_data)
        else:
            print(f"⚠️ Warning: Recipe ID '{recipe_id}' not found in dataset.")

    # 🩹 Fallback if LLM returned fewer recipes than needed
    if len(selected_recipes) < request.meals_per_day * request.days:
        import random
        remaining_needed = request.meals_per_day * request.days - len(selected_recipes)
        extra = random.choices(
            [get_recipe_by_id(RECIPES, r) for r in similar_recipes if get_recipe_by_id(RECIPES, r)],
            k=remaining_needed,
        )
        selected_recipes += extra

    # ✅ Just show the meals (concise output)
    print(f"🍽️ Selected meals for the plan:")
    for r in selected_recipes:
        print(f" - {r.get('title')}")

    # -----------------------
    # Step 8 – Attach images
    # -----------------------
    selected_recipes_with_images = [attach_recipe_images(r) for r in selected_recipes]

    # -----------------------
    # Step 9 – Structure plan by day
    # -----------------------
    plan = []
    for day in range(1, request.days + 1):
        start_idx = (day - 1) * request.meals_per_day
        end_idx = start_idx + request.meals_per_day
        plan.append({
            "day": day,
            "meals": selected_recipes_with_images[start_idx:end_idx],
        })

    # -----------------------
    # Step 10 – Return structured response
    # -----------------------
    return {
        "summary": {
            "days": request.days,
            "meals_per_day": request.meals_per_day,
            "preferences": request.preferences,
            "retrieved_recipes": len(recipe_context),
        },
        "plan": plan,
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
    Example: /recipe/cal-smart-tex-mex-beef-bowls
    """

    # Step 1: Find the recipe in the dataset
    recipe = get_recipe_by_id(RECIPES, recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Step 2: Attach recipe images (AI-generated or stored)
    recipe_with_images = attach_recipe_images(recipe)

    # Step 3: Return only the recipe information
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

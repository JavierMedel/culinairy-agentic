from fastapi import APIRouter, HTTPException
from utils.loader import get_recipe_by_id, attach_recipe_images
from utils.ai_agent import query_nim
import json

router = APIRouter()

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
        print("⚠️ AI recommendations failed, skipping. Error:", e)
        similar_recipes = []

    recipe_with_images["recommended_recipes"] = similar_recipes

    return recipe_with_images
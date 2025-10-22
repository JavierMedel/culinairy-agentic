import os
import json
from typing import List, Dict, Any

# Base path for images (relative to backend folder)
IMAGE_BASE_PATH = "images"
BASE_URL = "http://localhost:8000"  # used for FastAPI docs and frontend previews


def load_recipes_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load all recipes from a single JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both possible structures: a list or a dict containing 'recipes'
        if isinstance(data, dict) and "recipes" in data:
            return data["recipes"]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid JSON format: must be a list or contain a 'recipes' key.")

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error decoding JSON in {file_path}")
        return []


def get_recipe_by_id(recipes: list, recipe_id: str) -> dict:
    """
    Find a recipe by its 'id_legacy' or 'id' field.
    Returns an empty dict if not found.
    """
    for recipe in recipes:
        if recipe.get("id_legacy") == recipe_id or recipe.get("id") == recipe_id:
            return recipe
    return {}


def attach_recipe_images(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach full URLs for dish, cooking steps, and ingredient images.
    Uses FastAPI's /images static route for rendering in docs.
    """
    recipe = recipe.copy()

    # --- Dish Image ---
    dish_img = recipe.get("image_url")
    if dish_img:
        recipe["dish_image_url"] = f"{BASE_URL}/images/dish/{os.path.basename(dish_img)}"

    # --- Step Images ---
    if "steps" in recipe:
        for idx, step in enumerate(recipe["steps"]):
            step_img = step.get("image")
            if step_img:
                recipe["steps"][idx]["image_url"] = f"{BASE_URL}/images/cooking_step/{os.path.basename(step_img)}"

    # --- Ingredient Images ---
    if "ingredients" in recipe:
        for idx, ing in enumerate(recipe["ingredients"]):
            ing_img = ing.get("image")
            if ing_img:
                recipe["ingredients"][idx]["image_url"] = f"{BASE_URL}/images/ingredient/{os.path.basename(ing_img)}"

    return recipe

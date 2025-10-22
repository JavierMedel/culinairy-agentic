import os
import json
from typing import List, Dict, Any

# Base path for images (relative to backend folder)
IMAGE_BASE_PATH = "images"

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
    Add full relative paths for dish, cooking steps, and ingredient images.
    """
    recipe = recipe.copy()

    # Dish image
    dish_img = recipe.get("image_url")
    if dish_img:
        recipe["dish_image_url"] = os.path.join(IMAGE_BASE_PATH, "dish", os.path.basename(dish_img))

    # Step images
    if "steps" in recipe:
        for idx, step in enumerate(recipe["steps"]):
            step_img = step.get("image")
            if step_img:
                recipe["steps"][idx]["image_url"] = os.path.join(IMAGE_BASE_PATH, "cooking_step", os.path.basename(step_img))

    # Ingredient images
    if "ingredients" in recipe:
        for idx, ing in enumerate(recipe["ingredients"]):
            ing_img = ing.get("image")
            if ing_img:
                recipe["ingredients"][idx]["image_url"] = os.path.join(IMAGE_BASE_PATH, "ingredient", os.path.basename(ing_img))

    return recipe
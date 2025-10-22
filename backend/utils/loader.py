import json
from typing import List, Dict, Any

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
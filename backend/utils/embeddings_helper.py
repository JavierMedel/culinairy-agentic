import requests
import numpy as np

EMBEDDING_NIM_URL = "http://localhost:8001/v1/embeddings"  # your embeddings NIM

# In-memory storage for demo purposes
embedding_index = {}

def get_embedding(text: str):
    """
    Query the Retrieval Embedding NIM to get embeddings for a text.
    """
    payload = {
        "input": [text],
        "model": "nvidia/llama-3.2-nv-embedqa-1b-v2",
        "input_type": "query"
    }
    try:
        response = requests.post(EMBEDDING_NIM_URL, json=payload)
        response.raise_for_status()
        embedding = response.json()["data"][0]["embedding"]
        return np.array(embedding)
    except Exception as e:
        print("Error calling embeddings NIM:", e)
        return None
    

def add_recipe_embedding(recipe_id: str, text: str):
    """
    Add a recipe to the embedding index.
    """
    emb = get_embedding(text)
    if emb is not None:
        embedding_index[recipe_id] = emb
        # print("Embedding index contents:", embedding_index)
        return True
    
    return False


def find_similar_recipes(query_text: str, top_k: int = 3):
    """
    Find the most similar recipes based on cosine similarity.
    """
    query_emb = get_embedding(query_text)
    if query_emb is None or not embedding_index:
        return []

    similarities = []
    for rid, emb in embedding_index.items():
        sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
        similarities.append((rid, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return [rid for rid, _ in similarities[:top_k]]

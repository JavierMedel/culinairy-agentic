import requests
import json

# URL of your running embeddings NIM container
EMBEDDINGS_URL = "http://localhost:8001/v1/embeddings"


# Example input
texts = ["Hello world", "Give me 3 low-carb Mexican dinner ideas"]

payload = {
    "input": texts,
    "model": "nvidia/llama-3.2-nv-embedqa-1b-v2",
    "input_type": "query"
}

try:
    response = requests.post(EMBEDDINGS_URL, json=payload)
    response.raise_for_status()  # raise error if request failed
    embeddings = response.json()
    print(json.dumps(embeddings, indent=2))
except Exception as e:
    print("Error calling embeddings NIM:", e)

import os
import requests
import json

# Default endpoint for local NIM
NIM_URL = os.getenv("NIM_URL", "http://localhost:8000/v1/chat/completions")

def query_nim(prompt: str, temperature: float = 0.7) -> str:
    """
    Sends a prompt to the locally running NVIDIA NIM (Llama-3.1 Nemotron Nano 8B).
    """
    payload = {
        "model": "nvidia/llama-3.1-nemotron-nano-8b-v1",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant for meal planning and recipe generation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 300
    }

    try:
        response = requests.post(NIM_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        print(f"❌ Error querying NIM: {e}")
        return "AI service unavailable"
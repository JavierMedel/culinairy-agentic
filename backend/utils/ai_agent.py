import os
import requests
import json

# Load NVIDIA NIM endpoint and API key from environment variables
NIM_ENDPOINT = os.getenv("NIM_ENDPOINT", "https://your-nim-endpoint.aws.com/v1/completions")
NIM_API_KEY = os.getenv("NIM_API_KEY", "replace-with-your-key")

def query_nim(prompt: str, temperature: float = 0.7) -> str:
    """
    Send a reasoning prompt to the NVIDIA NIM Llama-3 model.
    Returns the model's output as a string.
    """

    if not NIM_ENDPOINT or not NIM_API_KEY:
        print("⚠️ NIM endpoint or API key not set in .env")
        return "NIM not configured. Using fallback."

    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3-1-nemotron-nano-8B-v1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 800,
    }

    try:
        response = requests.post(NIM_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ NIM query failed: {e}")
        return "NIM model unavailable. Using fallback."


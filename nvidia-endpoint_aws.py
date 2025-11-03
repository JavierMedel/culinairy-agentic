import requests
import json

# -----------------------------
# Configuration
# -----------------------------
NIM_URL = "http://ac848d2b77594435281c81d04a0230b6-51436228.us-east-1.elb.amazonaws.com:8000/v1/chat/completions"

# -----------------------------
# Payload
# -----------------------------
payload = {
    "model": "nvidia/llama-3.1-nemotron-nano-8b-v1",
    "messages": [
        {"role": "system", "content": "You are a polite and culinary assistant helping people with their meal planning."},
        {"role": "user", "content": "Give a detailed recipe for a Taco Mexican Steak with all preparation steps, ingredients, and cooking tips."}
    ],
    "max_tokens": 300,
    "top_p": 1,
    "n": 1,
    # "stream": True,   # enable streaming
    "stop": None,
    "frequency_penalty": 0.0
}

# -----------------------------
# Headers
# -----------------------------
headers = {
    "accept": "text/event-stream",  # important for SSE
    "Content-Type": "application/json"
}

# -----------------------------
# Make the POST request with streaming (SSE)
# -----------------------------
with requests.post(NIM_URL, headers=headers, json=payload, stream=True, timeout=300) as response:
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
    else:
        print("Assistant reply:\n")
        for line in response.iter_lines(decode_unicode=True):
            if line:
                # SSE lines start with "data: "
                if line.startswith("data: "):
                    data_str = line[len("data: "):].strip()
                    if data_str == "[DONE]":  # End of stream
                        break
                    try:
                        data_json = json.loads(data_str)
                        for choice in data_json.get("choices", []):
                            content = choice.get("delta", {}).get("content")
                            if content:
                                print(content, end="", flush=True)
                    except json.JSONDecodeError:
                        continue

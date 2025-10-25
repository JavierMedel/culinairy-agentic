from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")

res = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-nano-8b-v1",
    messages=[{"role": "user", "content": "Write a haiku about GenAI."}]
)
print(res.choices[0].message.content)

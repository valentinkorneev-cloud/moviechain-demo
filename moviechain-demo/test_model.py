import requests

GROQ_API_KEY = "GROQ_API_KEY"

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
    json={
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Привет!"}],
        "max_tokens": 10
    }
)

print(response.status_code)
print(response.json())

# Для теста: python C:\Users\NAMETAG\Desktop\moviechain-demo\test_model.py
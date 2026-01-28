import requests

GROQ_API_KEY = "GROQ_API_KEY"

def check_groq_key():
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Ключ Groq действителен!")
            models = [m['id'] for m in response.json().get('data', [])]
            print(f"Доступные модели (первые 5): {models[:5]}")
        else:
            print(f"❌ Ошибка: {response.status_code} — {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Ошибка подключения: {e}")
    except Exception as e:
        print(f"💥 Неизвестная ошибка: {e}")

if __name__ == "__main__":
    check_groq_key()


# Для проверки: python C:\Users\NAMETAG\Desktop\moviechain-demo\check_groq_key.py

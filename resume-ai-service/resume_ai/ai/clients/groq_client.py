import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL")   
GROQ_MODEL = os.getenv("GROQ_MODEL")      

def call_groq(prompt: str, max_tokens: int = 500, temperature: float = 0.2):
    """
    Calls Groq LLaMA model and returns improved text.
    This is a simple wrapper; more features will be added later.
    """

    if not GROQ_API_KEY:
        raise Exception("Missing GROQ_API_KEY in environment")
    
    url = f"{GROQ_API_URL}/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    response = requests.post(url, json=body, headers=headers, timeout=20)

    if response.status_code != 200:
        raise Exception(f"Groq API Error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]

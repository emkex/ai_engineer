'''
Сравнение скорости ответа: Ollama (llama3.2) vs Claude API (haiku)
на одинаковый запрос на английском.
'''

import time
import os
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CUR_DIR, '.env'))

PROMPT = "Explain what a large language model is in three sentences."

# --- Ollama ---
def call_ollama(prompt: str) -> tuple[str, float]:
    start = time.time()
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'llama3.2',
            'prompt': prompt,
            'stream': False,
        }
    )
    elapsed = time.time() - start
    return response.json()['response'], elapsed

# --- Claude API ---
def call_claude(prompt: str) -> tuple[str, float]:
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    start = time.time()
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.time() - start
    return message.content[0].text, elapsed


if __name__ == "__main__":
    print(f"Промпт: {PROMPT}\n")

    ollama_text, ollama_time = call_ollama(PROMPT)
    print(f"[Ollama llama3.2] ({ollama_time:.2f}s)")
    print(ollama_text.strip())

    print()

    claude_text, claude_time = call_claude(PROMPT)
    print(f"[Claude haiku-4-5] ({claude_time:.2f}s)")
    print(claude_text.strip())

    print()
    faster = "Ollama" if ollama_time < claude_time else "Claude"
    diff = abs(ollama_time - claude_time)
    print(f"Быстрее: {faster} на {diff:.2f}s")

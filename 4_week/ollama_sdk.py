'''
Вызов Ollama (llama3.2) через Anthropic SDK с stream=True.

Ollama поддерживает Anthropic Messages API (/v1/messages) нативно.
Anthropic SDK направляем на base_url='http://localhost:11434' — без /v1,
Ollama сам добавляет нужный путь.

Для сравнения: вот что возвращает Ollama напрямую через requests (stream=False):
{
  "model": "llama3.2",
  "created_at": "...",
  "response": "How can I assist you today?",   # <-- только плоская строка
  "done": true,
  "done_reason": "stop",
  "context": [128006, 9125, ...],              # токены как int-массив
  "total_duration": 19027312393,               # наносекунды
  "load_duration": 7945445352,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 9475807924,
  "eval_count": 8,
  "eval_duration": 1512694880
}

Через Anthropic SDK (нативный /v1/messages endpoint) ответ совсем другой:
- объект Message с .content[], .usage, .model, .stop_reason
- стриминг через TextEvent / ContentBlockDeltaEvent
- нет "context", нет наносекунд — зато есть usage.input_tokens / output_tokens
'''

import os
import anthropic
from dotenv import load_dotenv

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CUR_DIR, '.env'))

# Ollama нативно поддерживает Anthropic Messages API на /v1/messages
# base_url — без /v1, SDK сам добавит нужный путь
client = anthropic.Anthropic(
    api_key="ollama",                      # не проверяется, но обязательно
    base_url="http://localhost:11434",
)

SYSTEM = (
    "You are a concise financial data analyst. "
    "Always answer in 2-3 sentences. "
    "When discussing numbers, be precise."
)

PROMPT = "What is a large language model and how can it be applied in finance?"

print("=" * 60)
print("Модель: llama3.2 через Anthropic SDK → Ollama /v1/messages")
print(f"Промпт: {PROMPT}")
print("=" * 60)
print()

# stream=True — токены печатаются по мере генерации
with client.messages.stream(
    model="llama3.2",
    max_tokens=300,
    temperature=0.7,
    top_p=0.9,
    system=SYSTEM,
    messages=[
        {"role": "user", "content": PROMPT},
    ],
) as stream:
    print("[streaming response]")
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print("\n")
    final = stream.get_final_message()

# Покажем структуру финального Message-объекта — в отличие от requests-ответа
print("=" * 60)
print("Структура финального ответа (Anthropic Message object):")
print("=" * 60)
print(f"  .id            = {final.id}")
print(f"  .model         = {final.model}")
print(f"  .stop_reason   = {final.stop_reason}")
print(f"  .role          = {final.role}")
print(f"  .content       = {final.content}")
print()
print("  .usage:")
print(f"    .input_tokens  = {final.usage.input_tokens}")
print(f"    .output_tokens = {final.usage.output_tokens}")
print()
print("Через requests напрямую — только .response (строка) + длительности в нс.")
print("Через SDK — полноценный Message с типизированными блоками и usage.")

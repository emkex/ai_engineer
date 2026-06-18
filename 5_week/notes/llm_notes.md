# PydanticAI — один агент, разные модели

## Главная идея

PydanticAI — это слой оркестрации поверх любого инференса.
Агент, инструменты, structured output — всё одинаково.
Меняется только одна строчка: откуда берётся модель.

```
[твой код с агентом и схемами]
        ↓
[PydanticAI]
        ↓
[модель] ← вот здесь можно подставить что угодно
```

---

## Пример 1 — Anthropic Claude (облако)

```python
import asyncio
from pydantic import BaseModel
from pydantic_ai import Agent

class NewsItem(BaseModel):
    title: str
    sentiment: str        # bullish / bearish / neutral
    importance: int       # 1–5

# строка "anthropic:claude-haiku-4-5" — встроенный провайдер PydanticAI
agent = Agent(
    "anthropic:claude-haiku-4-5",
    output_type=NewsItem,
    system_prompt="Анализируй финансовую новость. Возвращай структуру."
)

async def main():
    result = await agent.run("Apple упала на 8% на фоне слабого отчёта.")
    print(result.output.title)      # str — гарантировано
    print(result.output.sentiment)  # bullish / bearish / neutral
    print(result.output.importance) # int 1–5

asyncio.run(main())
```

**Зависимости:**
```bash
pip install pydantic-ai anthropic
# ANTHROPIC_API_KEY в .env
```

---

## Пример 2 — Ollama (локально)

Ollama поднимает модель локально и даёт OpenAI-совместимый HTTP API на `localhost:11434`.
PydanticAI подключается к нему через встроенный `OllamaModel`.

```python
import asyncio
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel

class NewsItem(BaseModel):
    title: str
    sentiment: str
    importance: int

# OllamaModel — встроен в PydanticAI, указываем имя модели как в ollama list
model = OllamaModel("llama3.2")

agent = Agent(
    model,
    output_type=NewsItem,
    system_prompt="Анализируй финансовую новость. Возвращай структуру."
)

# Остальной код — идентичен примеру 1
async def main():
    result = await agent.run("Apple упала на 8% на фоне слабого отчёта.")
    print(result.output.sentiment)

asyncio.run(main())
```

**Зависимости:**
```bash
# 1. Установить Ollama: ollama.com/download
ollama pull llama3.2

# 2.
pip install pydantic-ai
# API_KEY не нужен
```

**Что происходит:** `OllamaModel` просто шлёт запрос на `http://localhost:11434/v1/chat/completions` — Ollama отвечает в OpenAI-формате, PydanticAI этого не замечает.

---

## Пример 3 — llama.cpp (максимальный контроль локально)

llama-cpp-python умеет поднять OpenAI-совместимый HTTP-сервер.
Дальше — то же самое что с Ollama, только указываешь свой порт.

```bash
# Запускаем сервер из llama.cpp (один раз в отдельном терминале)
python -m llama_cpp.server \
    --model ~/models/tinyllama-1.1b.Q4_K_M.gguf \
    --port 8000
```

```python
import asyncio
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI

class NewsItem(BaseModel):
    title: str
    sentiment: str
    importance: int

# PydanticAI не знает что это llama.cpp — видит обычный OpenAI-эндпоинт
client = AsyncOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"          # llama.cpp сервер не проверяет ключ
)
model = OpenAIModel("tinyllama", openai_client=client)

agent = Agent(
    model,
    output_type=NewsItem,
    system_prompt="Анализируй финансовую новость. Возвращай структуру."
)

async def main():
    result = await agent.run("Apple упала на 8% на фоне слабого отчёта.")
    print(result.output.sentiment)

asyncio.run(main())
```

**Зависимости:**
```bash
pip install pydantic-ai llama-cpp-python openai
```

---

## Схема: как пазлы собираются

```
Твой код (один и тот же агент + схемы)
│
├── "anthropic:claude-haiku"   → HTTPS → api.anthropic.com
│
├── OllamaModel("llama3.2")    → HTTP  → localhost:11434/v1
│                                         ↑
│                                     [Ollama процесс]
│                                     запускает llama.cpp внутри
│
└── OpenAIModel(client=...)    → HTTP  → localhost:8000/v1
                                          ↑
                                      [llama-cpp-python сервер]
                                      грузит .gguf напрямую
```

Ключ: Ollama и llama.cpp сервер оба притворяются OpenAI API.
Поэтому `OpenAIModel` работает с обоими. PydanticAI не знает разницы.

---

## Когда что выбирать

| Ситуация | Что брать |
|---|---|
| Нужно быстро, качество важно | Anthropic/OpenAI SDK напрямую или `"anthropic:..."` в PydanticAI |
| Локально, просто, privacy | Ollama + `OllamaModel` |
| Локально, максимум контроля (параметры, VRAM) | llama-cpp-python сервер + `OpenAIModel` |
| Структурированный вывод + типизация поверх любого | PydanticAI (навешиваешь сверху любого из выше) |
| Граф агента, паузы, human-in-the-loop | LangGraph поверх любого SDK |
| Файнтюнинг, обучение | PyTorch + transformers — другой мир |

---

## Почему всё называется через "llama"

Это история одного прорыва.

В **феврале 2023** Meta выпустила **LLaMA** (Large Language Model Meta AI) — первую мощную модель с открытыми весами. До этого GPT-3/4 были закрыты, доступны только через платный API. LLaMA изменила это: веса можно скачать и запустить самому.

Качество оказалось сравнимым с GPT-3, но модель была **твоей**. Это взорвало open-source сообщество. За следующие недели вокруг LLaMA построили целую экосистему:

- **llama.cpp** — Georgi Gerganov написал за несколько дней C++ инференс прямо для LLaMA, потом добавил GGUF-квантизацию чтобы запускать на CPU. Стал стандартом для локального запуска.
- **Ollama** — «Old Llama» по духу, дружелюбная обёртка над llama.cpp. Название прямая отсылка.
- **llama-cpp-python** — Python-биндинги к llama.cpp.
- **LlamaIndex** — фреймворк для RAG, изначально назван по LLaMA как главной опенсорс модели.
- **Alpaca** — Stanford файнтюнил LLaMA и назвал Alpaca (альпака — родственник ламы).
- **Vicuna, Guanaco, Orca** — другие файнтюны LLaMA, названы родственными животными.

Потом Meta выпустила **LLaMA 2** (2023), **LLaMA 3** (2024), **LLaMA 3.2** (2024) — каждая была событием в open-weights сообществе. Название закрепилось.

**GGUF** — формат квантизованных моделей, назван по инициалам Georgi Gerganov (GG) + Universal Format. Файлы с `.gguf` это те самые «сжатые» модели которые запускает llama.cpp и Ollama.

**Итог:** "llama" в названии = «работает с открытыми весами моделей в open-source экосистеме». Это маркер происхождения, не просто бренд.
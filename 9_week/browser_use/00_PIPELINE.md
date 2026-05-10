# Browser Use — Learning Pipeline (1.5–2 часа)

## Установка (5 мин)
```bash
source .venv/bin/activate
pip install browser-use
playwright install chromium
```

## Порядок изучения

| # | Файл | Время | Что делаем |
|---|------|-------|-----------|
| 1 | `01_browser_use_basics.py` | 20 мин | Запустить агента с Haiku, посмотреть что он делает |
| 2 | `02_with_ollama.py` | 20 мин | То же самое, но бесплатно через llama3.2 |
| 3 | `03_pydantic_browser_tool.py` | 20 мин | Дать браузер как инструмент PydanticAI агенту |
| 4 | `04_security_hitl.py` | 20 мин | Запустить HITL — агент будет спрашивать разрешение |
| 5 | `05_production/` | 15 мин | Посмотреть Docker-сборку, запустить вручную без Docker |
| 6 | `cheatsheet.html` | 5 мин | Открыть в браузере, прочитать ответы на вопросы |

## Команды для быстрого старта

```bash
# Файл 1 — Haiku (нужен ANTHROPIC_API_KEY в .env)
python 01_browser_use_basics.py

# Файл 2 — Ollama (локально, бесплатно)
python 02_with_ollama.py

# Файл 3 — PydanticAI + playwright напрямую
python 03_pydantic_browser_tool.py

# Файл 4 — HITL Security
python 04_security_hitl.py

# Файл 5 — Production (без Docker, просто запуск агента)
python 05_production/agent.py
```

## Что нужно наблюдать при запуске

- `01` / `02`: в терминале видны шаги агента — navigate, extract, click. Посмотри сколько шагов он делает.
- `03`: PydanticAI явно вызывает `fetch_page_content` как tool — видно в логах.
- `04`: При действии "click" агент спросит "Разрешить? [y/N]". Введи `n` — увидишь, что он остановится.
- `05`: В production-варианте прокси и секреты идут через env, не хардкодятся.

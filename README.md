# AI Engineer Journey

Публичный дневник обучения: от базового Python до уверенного использования AI-инструментов в работе.

---

## О проекте

10-месячный путь от исследователя, далёкого от программирования, до AI Engineer — с практическими проектами на каждом этапе.
Старт: март 2026. Финиш: январь 2027.
Основной план: [AI_Engineer_Plan.html](AI_Engineer_Plan.html) · [Portfolio](https://emkex.github.io/ai_engineer/AI_Engineer_Plan.html)

---

## Структура репозитория

```
ai_engineer/
│
├── 1_week/               # Python: основы, функции, типы
├── 2_week/               # ООП: классы, наследование, dataclasses, SOLID
├── 3_week/               # Файлы, HTTP/REST, парсинг, Anthropic SDK
├── 4_week/               # Локальные LLM: Ollama, сравнение моделей
├── 5_week/               # ML: линейная регрессия, pandas, трансформеры
├── 6_week/               # RAG, ChromaDB, градиентный спуск (Adam), SVD/PCA
├── 7_week/               # Docker: образы, Dockerfile, Compose, контейнер-парсер
│   └── docker_lesson/
│       └── Parser/       # Контейнеризованный парсер с RabbitMQ + MongoDB
│
├── AI_Engineer_Plan.html # Мастер-план (портфолио)
└── requirements.txt      # Зависимости
```

---

## Стек (планируемый)

| Фаза | Период | Технологии |
|------|--------|------------|
| Основы | мар–апр | Python, Git, Anthropic API, Ollama, pandas, asyncio |
| Агентные системы | апр–май | LangGraph, PydanticAI, Qdrant, Docker, MCP, n8n |
| Деплой | июн | Docker Compose, PostgreSQL, nginx, LangSmith / Langfuse |
| Fine-tuning | июл–авг | HuggingFace, PEFT / LoRA, Claude Vision (multimodal) |
| Коммерциализация | сен–дек | Kubernetes, CI/CD, клиентские проекты |

---

## Как запустить

```bash
# Клонировать и активировать окружение
git clone https://github.com/emkex/ai_engineer.git
cd ai_engineer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Создать .env с ключами (не коммитить!)
cp .env.example .env  # при наличии шаблона

# Запустить конкретный скрипт
python 3_week/anthropic_sdk.py

# Jupyter notebooks
jupyter notebook 5_week/lin_regr_ols_gd_practice.ipynb

# Docker (неделя 7)
cd 7_week/docker_lesson
docker build -t hello .
docker run hello

# Docker Compose (парсер)
cd 7_week/docker_lesson/Parser
docker compose up --build
```

---

## Автор

Telegram: [@em_kex](https://t.me/em_kex)
Email: emkexgg@gmail.com

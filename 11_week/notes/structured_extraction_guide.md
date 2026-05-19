# Structured Extraction: Pydantic AI, Optional поля, Prompt Caching, Память

## 1. Как работает structured output в Pydantic AI

Да, понял правильно. Когда вызываешь LLM через Pydantic AI, можно передать класс-схему и модель вернёт объект этого класса — не строку, а готовый Python-объект.

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class NewsItem(BaseModel):
    title: str
    source: str
    importance: int       # от 1 до 5
    topic: str
    confirmed: bool

agent = Agent(
    model="claude-sonnet-4-5",
    result_type=NewsItem   # вот это и есть structured output
)

result = await agent.run("Вот текст новости: ...")
print(result.data.title)      # уже готовый объект, не JSON-строка
print(result.data.importance)
```

Под капотом Pydantic AI:
1. Превращает схему класса в JSON Schema
2. Передаёт в промпт или через tool_use Anthropic
3. Парсит ответ обратно в объект
4. Если валидация не прошла — автоматически делает retry с сообщением об ошибке

**Проблема:** если в тексте нет данных для поля, модель придумывает. Потому что схема требует значение — модель обязана что-то поставить.

---

## 2. Optional поля — что это и как работают

`Optional[X]` в Python означает: поле может быть `X` или `None`. Модели явно разрешено вернуть null если данных нет.

**Без Optional — модель галлюцинирует:**
```python
class ArticleData(BaseModel):
    title: str
    author: str       # обязательное поле
    date: str         # обязательное поле
    summary: str      # обязательное поле
```
Если в тексте нет автора — модель напишет "Unknown Author" или придумает имя. Схема требует строку, null недопустим.

**С Optional — модель возвращает None:**
```python
from typing import Optional
from pydantic import BaseModel, Field

class ArticleData(BaseModel):
    title: str                          # обязательное — заголовок всегда есть
    author: Optional[str] = None        # может не быть
    date: Optional[str] = None          # может не быть
    summary: str                        # обязательное — резюме всегда нужно
    importance: Optional[int] = Field(
        default=None,
        description="1-5, только если явно указана важность в тексте"
    )
```

Теперь если автора нет — `author = None`, не галлюцинация.

**Промпт к этому:**
```
Extract data from the text below.
IMPORTANT: If a field is not explicitly stated in the text, return null.
Do NOT infer, guess, or assume values that are not present.
Only extract what is literally written.
```

**Полный пример с реальным текстом:**
```python
from typing import Optional, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent

class CompanyMention(BaseModel):
    name: str
    ticker: Optional[str] = Field(
        default=None,
        description="Stock ticker if mentioned, else null"
    )
    sentiment: Optional[str] = Field(
        default=None,
        description="positive/negative/neutral if assessable, else null"
    )
    price_mentioned: Optional[float] = Field(
        default=None,
        description="Price in USD if explicitly stated, else null"
    )

class NewsExtraction(BaseModel):
    companies: List[CompanyMention]
    main_topic: str
    has_market_impact: Optional[bool] = None

agent = Agent(
    model="claude-sonnet-4-5",
    result_type=NewsExtraction,
    system_prompt="""
    Extract structured data from financial news.
    Return null for any field not explicitly present in the text.
    Never guess or infer values.
    """
)
```

---

## 3. Prompt Caching — как работает

**Суть:** при повторных запросах с одинаковым началом промпта Anthropic не обрабатывает его заново — берёт из кеша. Платишь только за output-токены.

**Где помогает при extraction:**
- Большой документ (100+ страниц PDF) передаётся один раз, кешируется
- Каждый следующий запрос по этому документу — быстрее и дешевле
- Можно позволить себе детальный системный промпт с примерами

**Цены Anthropic:**
- Обычные input токены: $3 / 1M
- Запись в кеш (cache write): $3.75 / 1M (чуть дороже первый раз)
- Чтение из кеша (cache read): $0.30 / 1M (в 10 раз дешевле!)

**Как включить — прямой вызов Anthropic API:**
```python
import anthropic

client = anthropic.Anthropic()

# Большой документ — кешируем
document_text = open("big_report.txt").read()  # например 50 000 токенов

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1000,
    system=[
        {
            "type": "text",
            "text": "You are an expert financial analyst. Extract structured data.",
            "cache_control": {"type": "ephemeral"}  # кешируем системный промпт
        }
    ],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": document_text,
                    "cache_control": {"type": "ephemeral"}  # кешируем документ
                },
                {
                    "type": "text",
                    "text": "Extract all company mentions with sentiment."
                    # этот вопрос НЕ кешируем — он меняется
                }
            ]
        }
    ]
)

# В ответе можно проверить что попало в кеш:
print(response.usage.cache_creation_input_tokens)  # сколько записано
print(response.usage.cache_read_input_tokens)       # сколько прочитано из кеша
```

**Второй запрос к тому же документу — уже быстрее:**
```python
# Тот же документ + другой вопрос
response2 = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1000,
    system=[...],  # тот же системный промпт с cache_control
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": document_text,
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": "Now extract all risk factors mentioned."
                    # новый вопрос, документ берётся из кеша
                }
            ]
        }
    ]
)
# cache_read_input_tokens будет > 0 — значит кеш сработал
```

**Важные ограничения:**
- Кеш живёт 5 минут (ephemeral) — потом сбрасывается
- Минимум для кеширования: 1024 токена (Sonnet/Opus)
- Кешируется только начало промпта — изменяемая часть должна быть в конце

**Практический паттерн для extraction:**
```
[КЕШИРУЕТСЯ]
- Системный промпт с инструкциями
- Весь большой документ
- Few-shot примеры (текст → JSON)

[НЕ КЕШИРУЕТСЯ]
- Конкретный вопрос по документу
- Запрашиваемая схема
```

---

## 4. Память агентов (все варианты)

Строго говоря, "MEMO" как единый стандарт не существует. Это собирательное название паттернов долгосрочной памяти. Вот все варианты:

---

### 4.1 In-context memory (краткосрочная, в контексте)

Самая простая — весь контекст диалога передаётся в каждом запросе.

```python
# LangGraph — state хранит историю
from langgraph.graph import StateGraph, MessagesState

def agent_node(state: MessagesState):
    # state["messages"] — вся история разговора
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
```

**Ограничение:** контекстное окно конечно (~200K токенов у Claude). При длинных сессиях — обрезается или дорожает.

---

### 4.2 External memory — векторная БД (долгосрочная)

Воспоминания хранятся как embeddings в Qdrant/ChromaDB. При новом запросе ищешь релевантные.

```python
from qdrant_client import QdrantClient
from anthropic import Anthropic

client = QdrantClient(":memory:")
anthropic_client = Anthropic()

def save_to_memory(text: str, metadata: dict):
    """Сохранить факт в долгосрочную память"""
    # Получаем embedding через API
    embedding = get_embedding(text)  # любой embedding model
    client.upsert(
        collection_name="agent_memory",
        points=[{
            "id": generate_id(),
            "vector": embedding,
            "payload": {"text": text, **metadata}
        }]
    )

def recall_from_memory(query: str, top_k: int = 5) -> list:
    """Вспомнить релевантное"""
    query_embedding = get_embedding(query)
    results = client.search(
        collection_name="agent_memory",
        query_vector=query_embedding,
        limit=top_k
    )
    return [r.payload["text"] for r in results]

# В агенте:
def process_with_memory(user_message: str):
    # 1. Вспоминаем релевантное
    memories = recall_from_memory(user_message)
    
    # 2. Добавляем в контекст
    memory_context = "\n".join(memories)
    
    # 3. Вызываем модель
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=f"Relevant past context:\n{memory_context}",
        messages=[{"role": "user", "content": user_message}]
    )
    
    # 4. Сохраняем новое воспоминание
    save_to_memory(user_message, {"type": "user_input"})
    save_to_memory(response.content[0].text, {"type": "agent_response"})
    
    return response
```

---

### 4.3 Summary memory (сжатие истории)

При длинном диалоге — периодически сжимаешь старую историю в резюме.

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def summarize_history(messages: list, llm) -> str:
    """Сжать историю в краткое резюме"""
    history_text = "\n".join([
        f"{m.type}: {m.content}" for m in messages
    ])
    
    summary_prompt = f"""
    Summarize this conversation history in 3-5 key points.
    Focus on facts, decisions, and important context.
    
    History:
    {history_text}
    """
    
    response = llm.invoke([HumanMessage(content=summary_prompt)])
    return response.content

# В LangGraph — автоматическое сжатие при превышении лимита
def manage_memory(state: MessagesState, max_messages: int = 20):
    messages = state["messages"]
    
    if len(messages) > max_messages:
        # Сжимаем старые сообщения
        old_messages = messages[:-10]  # всё кроме последних 10
        recent_messages = messages[-10:]
        
        summary = summarize_history(old_messages, llm)
        summary_message = SystemMessage(
            content=f"Previous conversation summary: {summary}"
        )
        
        return {"messages": [summary_message] + recent_messages}
    
    return state
```

---

### 4.4 Entity memory (память о сущностях)

Отдельное хранилище фактов о конкретных сущностях — компаниях, людях, событиях.

```python
# Простая реализация через dict
entity_memory = {}

def update_entity_memory(entity_name: str, new_fact: str):
    if entity_name not in entity_memory:
        entity_memory[entity_name] = []
    entity_memory[entity_name].append(new_fact)

def get_entity_context(entity_name: str) -> str:
    facts = entity_memory.get(entity_name, [])
    return f"Known facts about {entity_name}: " + "; ".join(facts)

# Пример для «Задумки по экономике»:
update_entity_memory("Газпром", "Q3 2024: выручка упала на 15%")
update_entity_memory("Газпром", "CEO подал в отставку в ноябре 2024")

# При новом упоминании Газпрома — добавляем контекст:
context = get_entity_context("Газпром")
# "Known facts about Газпром: Q3 2024: выручка упала на 15%; CEO подал в отставку"
```

---

### 4.5 LangGraph checkpointing (персистентная память между сессиями)

LangGraph умеет сохранять полный state графа между запусками.

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, MessagesState

# Персистентное хранилище
memory = SqliteSaver.from_conn_string("agent_memory.db")

# Граф с checkpointing
graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")

app = graph.compile(checkpointer=memory)

# Каждый запрос с одинаковым thread_id продолжает тот же диалог
config = {"configurable": {"thread_id": "user_123"}}

# Первый запрос
result1 = app.invoke(
    {"messages": [HumanMessage("Расскажи про инфляцию")]},
    config=config
)

# Второй запрос — агент помнит первый
result2 = app.invoke(
    {"messages": [HumanMessage("А что с этим делать?")]},
    config=config  # тот же thread_id = та же память
)
```

---

### 4.6 Semantic / Episodic memory (паттерн из когнитивной науки)

Разделение памяти по типам — как у человека:

```python
# Семантическая память — общие факты ("Газпром — газовая компания")
# Эпизодическая память — конкретные события ("12 мая спросил про Газпром")

class AgentMemory:
    def __init__(self, qdrant_client):
        self.client = qdrant_client
    
    def store_semantic(self, fact: str):
        """Общий факт, долгоживущий"""
        self._store(fact, memory_type="semantic", ttl=None)
    
    def store_episodic(self, event: str):
        """Конкретное событие, может устаревать"""
        self._store(event, memory_type="episodic", ttl=30)  # 30 дней
    
    def recall(self, query: str, memory_type: str = None) -> list:
        """Поиск по памяти с фильтрацией по типу"""
        filters = {}
        if memory_type:
            filters["memory_type"] = memory_type
        return self._search(query, filters)
```

---

## 5. Итоговая таблица — когда что использовать

| Инструмент | Когда использовать | Сложность |
|---|---|---|
| Optional поля | Всегда при extraction | Низкая |
| Строгий промпт ("return null") | Всегда | Низкая |
| Temperature = 0 | Всегда при extraction | Низкая |
| Validation loop (PydanticAI retry) | При сложных схемах | Низкая |
| Prompt caching | Большой документ + много вопросов | Средняя |
| In-context memory | Короткие сессии | Низкая |
| Summary memory | Длинные диалоги | Средняя |
| Vector DB memory | Долгосрочная, между сессиями | Высокая |
| LangGraph checkpointing | Персистентный агент | Средняя |
| Entity memory | Трекинг конкретных объектов | Средняя |

---

## 6. Двухшаговый extraction — самый надёжный паттерн

Вместо "один вызов → сразу JSON" делаешь два шага:

```python
async def reliable_extraction(document: str, schema_class: BaseModel) -> BaseModel:
    
    # Шаг 1: Свободное извлечение фактов
    facts_agent = Agent(model="claude-sonnet-4-5", result_type=str)
    facts_result = await facts_agent.run(
        f"""
        Read this document and list ALL facts you can find.
        Be literal — only facts explicitly stated in text.
        
        Document:
        {document}
        """
    )
    
    # Шаг 2: Структурирование найденных фактов
    struct_agent = Agent(
        model="claude-sonnet-4-5",
        result_type=schema_class,
        system_prompt="Convert the facts below into the required schema. "
                      "Return null for any field not present in the facts."
    )
    result = await struct_agent.run(facts_result.data)
    return result.data
```

Двухшаговый подход снижает галлюцинации потому что на шаге 2 модель работает с уже выделенными фактами, а не с сырым текстом. Придумывать сложнее когда уже есть список.


------

# Где крутится агент и как стыкуется MCP

## Dify
**Роль:** приложения на базе LLM, RAG, публикация flow

**Суть:** хорошо для демо и прототипа. Встроенная RAG — загрузил PDF, сразу работает. Удобен как база знаний + конвейер: спарсерить данные, вытащить из базы знаний, прогнать через LLM.

ДЕЛАМ КОЛЛАБОРАЦИЮ МЕЖДУ DIFY & PYTHON CODE with API !!!

**Не для прода** — высокий latency (~2–3 сек), ограниченный контроль над логикой.

**До продакшена зафиксировать (скрин):**
- Редакция OSS или Cloud и кто инициирует исходящий вызов MCP
- Нужен ли обратный контур «ваше приложение как MCP server»
- Матрица прав: кто из ролей может дёрнуть какой инструмент

---

## n8n
**Роль:** интеграции, webhooks, AI Agent (LangChain)

**Суть:** workflow-engine, не LLM-native — но LLM-node встроен. Главная сила — разграничения по департаментам и ролям (каждый department видит только свои workflows и credentials) + хороший оркестратор событий. Webhook-first: событие (письмо, Telegram, Asana) → routing → LLM → действие.

**До продакшена зафиксировать (скрин):**
- Где лежат токены: Credential Manager, vault, переменные среды
- MCP через HTTP или прокси: граница сети и allowlist исходящих хостов
- Как фиксируется версия контракта при обновлении ноды

---

## AWS Bedrock (AgentCore)
**Роль:** корпоративные агенты, AgentCore

**Суть:** managed LLM-агенты от AWS. Безопасность через IAM roles + VPC isolation. Для HIPAA/FedRAMP. Дорого, vendor lock-in, сложная настройка.

**До продакшена зафиксировать (скрин):**
- Identity для вызовов и MCP proxy в AgentCore
- VPC endpoints и маршрут трафика к MCP
- Лимиты вызовов и бюджет на шаг в design doc

---

## Microsoft Copilot Studio
**Роль:** процессы в контуре M365

**Суть:** глубоко вшит в M365 (Teams, Outlook, Excel). Подходит только если весь стек Microsoft. Ограниченные кастомные модели, дорого.

**До продакшена зафиксировать (скрин):**
- Каталог коннекторов и классификация данных по чувствительности
- Что может покинуть тенант в сторону внешнего MCP
- Что остаётся внутри облака Microsoft

---

## Flowise
**Роль:** визуальные цепочки LangChain

**Суть:** open-source, бесплатно, быстрое прототипирование LangChain-пайплайнов. Молодой проект — стабильность и документация не всегда на уровне.

**До продакшена зафиксировать (скрин):**
- Есть ли стабильная MCP интеграция в вашей мажорной версии
- План обновлений при смене major у зависимостей
- Кто владеет конфигом endpoints в проде

---

## Langflow
**Роль:** визуальные потоки и агенты на базе LangChain

**Суть:** open-source, drag-and-drop граф агента. Хорош для быстрой итерации и понимания архитектуры визуально. Проблема — контроль версий зависимостей при переходе на прод.

**До продакшена зафиксировать (скрин):**
- Узел MCP в графе: кто разрешён на побочные эффекты и куда уходит сеть
- Воспроизводимый экспорт flow и закрепление версий зависимостей
- Разводка dev и prod по credentials и исходящим хостам

---

## Итог одной строкой

| Платформа | Когда брать |
|---|---|
| Dify | Быстрый прототип, демо клиенту, RAG-конвейер |
| n8n | Интеграции между системами, routing по департаментам |
| AWS Bedrock | Корпоратив, compliance, весь стек AWS |
| MS Copilot Studio | Весь стек Microsoft, M365 процессы |
| Flowise | Open-source эксперименты, обучение |
| Langflow | Прототипирование агентов визуально, dev-среда |

**Для «Задумки по экономике»:** n8n как оркестратор источников данных + Langflow/Flowise для визуального понимания архитектуры на этапе проектирования. В проде — чистый Python + LangGraph.


--------

## Что такое Toloka

Голландская компания, платформа для разметки данных (data annotation) с краудсорсингом. Клиенты — Amazon, Microsoft, Anthropic, Shopify. Основана в 2014, изначально как краудсорсинг для разметки данных для ML-моделей.

**Как работает:**

LLM интегрированы в пайплайн разметки на нескольких уровнях: LLM размечает всё автоматически → эксперты-люди проверяют качество. Или LLM размечает часть, люди — остаток. Или LLM подсказывает людям-аннотаторам.

**Ключевое отличие от того что ты описал:** это не инструмент для чанкинга текста перед подачей в LLM. Это платформа для создания обучающих данных — люди + LLM размечают тексты, изображения, аудио чтобы потом обучать/файн-тюнить модели.

**То что ты описывал** (LLM размечает текст и получаются читаемые чанки) — это больше про **semantic chunking**, который делается через LangChain/LlamaIndex. Там LLM анализирует структуру документа и нарезает его по смысловым границам, а не по фиксированному количеству токенов. Это отдельная тема от Toloka.

Возможно в уроке упоминали Toloka как пример того что LLM используют для разметки — и ты связал с чанкингом. Это разные вещи.

------

**Простейший прод**

n8n имеет собственную лицензию (fair-code / Sustainable Use License) — нельзя просто взять n8n и продавать как свой продукт.

задача: мы не продаём n8n, мы интеграторы. Берём задачу клиента и собираем решение где n8n — один из компонентов.

---

**Архитектура которую описывают**

```
Пользователь
    ↓
Open WebUI  ← красивый интерфейс, там же права доступа по ролям
    ↓
Python-прослойка  ← ~1000 строк, своя логика, валидация, роутинг
    ↓
n8n  ← оркестратор: webhook принял → workflow запустил → инструменты дёрнул
    ↓
Внешние сервисы (API, БД, LLM и тд)
```

**Почему именно так:**

Open WebUI — это ChatGPT-like интерфейс с системой пользователей и ролей. Там можно создать юзера, назначить ему права. Но Open WebUI сам по себе не умеет сложную бизнес-логику.

Python-прослойка — мост. Принимает запрос из Open WebUI, проверяет кто пришёл и что ему можно, формирует webhook-запрос в n8n.

n8n — получает чистый запрос уже с контекстом "кто это и что хочет" и запускает нужный workflow. Разграничение прав уже применено до него — n8n просто выполняет.

**Ключевая мысль:** права настраиваются один раз в Open WebUI, Python-прослойка их транслирует, n8n их не знает и не проверяет — он просто получает уже авторизованный запрос. Это чистая архитектура.

**1000 строк + n8n = прод с 1000 RPS** — это про то что не надо писать весь оркестратор с нуля. n8n берёт на себя визуальные workflow, retry, очереди, интеграции. Python только клей и бизнес-логика. Отсюда малый объём кода при серьёзной нагрузке.
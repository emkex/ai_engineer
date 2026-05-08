"""
ФАЙЛ 5: Продвинутые архитектуры — Query Expansion, Multi-hop, Agentic RAG, GraphRAG
======================================
Документация: https://langchain-ai.github.io/langgraph/
Слайды: 13–18, 22
"""

import os
import numpy as np
import anthropic
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

load_dotenv()

# Финансовый корпус (полный — 15 документов)
KNOWLEDGE_BASE = [
    {"ticker": "SBER",  "date": "2026-04-15", "source": "РБК",
     "content": "Сбербанк: чистая прибыль Q1 2026 = 432 млрд руб (+18% г/г). NIM=5.8%. Дивиденды: 50% от прибыли МСФО. Целевая цена аналитиков: 380 руб."},
    {"ticker": "GAZP",  "date": "2026-03-20", "source": "Интерфакс",
     "content": "Газпром: выручка 2025 = 8.2 трлн руб (-12%). EBITDA=2.4 трлн. ND/EBITDA=3.1x. Дивиденды не рекомендованы. Экспорт газа в Европу -23%."},
    {"ticker": "YNDX",  "date": "2026-04-28", "source": "Ведомости",
     "content": "Яндекс: выручка 2025 = 1.1 трлн руб (+38%). Поиск: 680 млрд руб. YandexGPT топ-5 мировых LLM. Прогноз 2026: +35-40%. Целевая цена: 5200 руб."},
    {"ticker": "NVDA",  "date": "2026-02-26", "source": "Reuters",
     "content": "NVIDIA Q4 FY2026: revenue $39.3B (+78% YoY). Data Center: $35.6B. Gross margin 73.5%. EPS $0.89. Next quarter guidance $43B. Analyst target $1200."},
    {"ticker": "AAPL",  "date": "2026-02-01", "source": "Bloomberg",
     "content": "Apple Q1 FY2026: revenue $124.3B (+4%). iPhone $69.1B. Services $26.3B (+14%). EPS $2.40. Buyback $90B. Dividend $0.25/share."},
    {"ticker": "TSLA",  "date": "2026-01-29", "source": "CNBC",
     "content": "Tesla Q4 2025: deliveries 495k vehicles (-8% QoQ). Revenue $25.7B. Automotive gross margin 17.6%. Energy business $3.1B (+87%). FSD v14: 400k users."},
    {"ticker": "LKOH",  "date": "2026-04-10", "source": "Коммерсантъ",
     "content": "ЛУКОЙЛ 2025: выручка 9.1 трлн руб (-5%). EBITDA 1.8 трлн. FCF 950 млрд. Дивиденды: 1100 руб/акция. ND/EBITDA=0.1x. Buyback 25 млрд."},
    {"ticker": "MGNT",  "date": "2026-03-05", "source": "РБК",
     "content": "Магнит: 850 новых магазинов в 2025. Выручка LFL +6.8%. Маркетплейс Magnum: 2.3 млн покупателей. Операционная прибыль 280 млрд. Дивиденды рассматриваются."},
    {"ticker": "ALRS",  "date": "2026-02-14", "source": "Интерфакс",
     "content": "АЛРОСА: продажи алмазов +12% январь 2026. Цены стабилизировались. Прогноз добычи 2026: 34.5 млн карат. Рассматривается листинг в Дубае."},
    {"ticker": "META",  "date": "2026-01-29", "source": "WSJ",
     "content": "Meta Q4 2025: revenue $48.4B (+21% YoY). Net income $20.8B. DAU 3.35B. AI ads boosted ARPU +18%. Reality Labs loss $5.1B. Llama 4 released."},
    {"ticker": "ROSN",  "date": "2026-04-20", "source": "Ведомости",
     "content": "Роснефть: Восток Ойл первая фаза завершена. Добыча: 500 тыс баррелей/сутки. Opex $4.5/баррель. Полная мощность 2 млн баррелей/сутки к 2030."},
    {"ticker": "GMKN",  "date": "2026-03-18", "source": "Коммерсантъ",
     "content": "Норникель 2025: никель 193 тыс тонн (-4%). Палладий 2.85 млн тройских унций. Выручка 1.4 трлн руб. Дивиденды: 1400 руб/акция."},
    {"ticker": "MSFT",  "date": "2026-01-29", "source": "Bloomberg",
     "content": "Microsoft Q2 FY2026: revenue $69.6B (+12%). Azure +31% YoY. Copilot: 45M subscribers. Net income $24.1B. OpenAI investment +$15B."},
    {"ticker": "POSI",  "date": "2026-04-22", "source": "РБК",
     "content": "Positive Technologies 2025: отгрузки 32 млрд руб (+35%). NPS 12 млрд руб (+60%). Прогноз 2026: 40-45 млрд. Дивиденды: 20 руб/акция."},
    {"ticker": "OZON",  "date": "2026-03-12", "source": "Ведомости",
     "content": "Ozon 2025: GMV 3.1 трлн руб (+62%). Заказы 1.2 млрд (+55%). Fintech кредитный портфель 280 млрд. EBITDA впервые +25 млрд. Покупателей 58 млн."},
]


def to_text(doc: dict) -> str:
    """Преобразует документ в строку для embedding."""
    return f"[{doc['ticker']}] {doc['date']} ({doc['source']}): {doc['content']}"


corpus = [to_text(doc) for doc in KNOWLEDGE_BASE]

# Загружаем модель и строим базовый векторный индекс
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("Векторизация корпуса...")
corpus_embeddings = embed_model.encode(corpus, show_progress_bar=False)


def vector_search(query: str, top_k: int = 5) -> list[dict]:
    """Базовый векторный поиск — используется во всех архитектурах."""
    query_vec = embed_model.encode([query])
    scores = cosine_similarity(query_vec, corpus_embeddings)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [
        {"idx": int(i), "doc": KNOWLEDGE_BASE[i], "text": corpus[i], "score": float(scores[i])}
        for i in top_indices
    ]


# =============================================================================
# ШАГ 1: QUERY EXPANSION — расширение запроса
#
# ЧТО ЕСТЬ: короткий запрос пользователя ("дивиденды сбер")
# ЧТО ДЕЛАЕМ: расширяем запрос N вариантами для улучшения полноты поиска
# КАК РАБОТАЕТ:
#   Проблема: пользователь пишет коротко → теряем релевантные документы
#   HyDE (Hypothetical Document Embeddings): генерируем гипотетический ответ,
#   ищем по его вектору — он ближе к реальным документам чем короткий запрос
#   Multi-query: N разных формулировок → объединяем результаты
#
# Слайд 22: «Query Expansion: один запрос → несколько → больше релевантных документов»
# =============================================================================

def expand_query(original_query: str, n_variants: int = 3) -> list[str]:
    """
    Генерирует варианты запроса через Claude Haiku.

    Слайд 22: Multi-query expansion — больше вариантов → выше recall.
    Трейдоф: N вариантов × время поиска = выше задержка.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content":
            f"Ты помощник финансового аналитика. "
            f"Сгенерируй {n_variants - 1} альтернативных поисковых запроса для финансового RAG.\n"
            f"Оригинальный запрос: '{original_query}'\n\n"
            f"Требования:\n"
            f"- Каждый вариант на отдельной строке\n"
            f"- Без нумерации и маркеров\n"
            f"- Используй синонимы финансовых терминов (прибыль/доход/earnings, "
            f"дивиденды/выплаты/distributions, выручка/оборот/revenue)\n"
            f"- Варианты должны искать ТУ ЖЕ информацию, просто другими словами"}],
    )
    variants = [original_query]
    for line in response.content[0].text.strip().split("\n"):
        line = line.strip().lstrip("-•123456789. ")
        if line and line.lower() != original_query.lower():
            variants.append(line)
    return variants[:n_variants]


def expanded_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Поиск по расширенному набору запросов с дедупликацией.
    Для каждого варианта запроса — поиск, затем объединяем уникальные документы.
    Лучший score для каждого документа (если попался по нескольким запросам).
    """
    all_results: dict[int, dict] = {}

    for q_variant in expand_query(query):
        for r in vector_search(q_variant, top_k=top_k):
            idx = r["idx"]
            # Сохраняем максимальный score по всем вариантам запроса
            if idx not in all_results or r["score"] > all_results[idx]["score"]:
                all_results[idx] = r

    # Сортируем по убыванию score
    return sorted(all_results.values(), key=lambda x: x["score"], reverse=True)[:top_k]


print("\n=== Query Expansion ===")
original = "дивиденды Сбербанка"
variants = expand_query(original, n_variants=3)
print(f"Оригинальный запрос: '{original}'")
for i, v in enumerate(variants, 1):
    print(f"  Вариант {i}: '{v}'")

expanded_results = expanded_search("дивиденды российских компаний", top_k=3)
print(f"\nExpanded search результаты (top-3):")
for r in expanded_results:
    print(f"  [{r['doc']['ticker']}] score={r['score']:.3f}")


# =============================================================================
# ШАГ 2: MULTI-HOP RETRIEVAL — итеративный поиск
#
# ЧТО ЕСТЬ: сложный вопрос, требующий нескольких шагов поиска
# ЧТО ДЕЛАЕМ: итеративно уточняем поиск на основе найденного
# КАК РАБОТАЕТ:
#   "Какой тикер с лучшей маржой также платит высокие дивиденды?"
#   Hop 1: ищем компании с высокой маржой
#   Hop 2: среди найденных — ищем данные по дивидендам
#   Каждый hop уточняет следующий запрос
#
# Слайд 22: «Multi-hop: цепочка поиска для сложных аналитических вопросов»
# =============================================================================

def multi_hop_retrieve(query: str, max_hops: int = 2) -> list[dict]:
    """
    Итеративный поиск: каждый hop уточняет предыдущий.

    Параметры:
        query: исходный сложный вопрос
        max_hops: максимальное число итераций поиска
    """
    current_query = query
    all_contexts: list[dict] = []
    seen_indices: set[int] = set()

    print(f"\n  Multi-hop для: '{query}'")

    for hop in range(max_hops):
        results = vector_search(current_query, top_k=3)

        # Добавляем только новые документы (дедупликация по индексу)
        new_results = [r for r in results if r["idx"] not in seen_indices]
        all_contexts.extend(new_results)
        seen_indices.update(r["idx"] for r in new_results)

        print(f"  Hop {hop+1}: запрос='{current_query[:50]}...' "
              f"→ найдено {len(new_results)} новых документов")

        # Следующий запрос формируется на основе найденного тикера
        # В production: LLM анализирует найденные документы и формулирует следующий вопрос
        if results:
            found_ticker = results[0]["doc"]["ticker"]
            # Mock: следующий поиск по связанным данным первого найденного тикера
            if hop == 0:
                current_query = f"{found_ticker} дивиденды дивидендная доходность выплаты"
            else:
                current_query = f"{found_ticker} финансовые риски долговая нагрузка"

    return all_contexts


print("\n=== Multi-hop Retrieval ===")
multi_results = multi_hop_retrieve(
    "Какие компании с высокой маржой EBITDA также платят дивиденды?",
    max_hops=2,
)
print(f"Всего найдено документов за {2} hops: {len(multi_results)}")
for r in multi_results:
    print(f"  [{r['doc']['ticker']}] {r['doc']['content'][:60]}...")


# =============================================================================
# SUMMARY 1: Шаги 1-2
# Query Expansion: больше вариантов запроса → выше полнота (recall).
# Трейдоф: больше поисков → выше задержка и шанс нерелевантных результатов.
# Multi-hop: для аналитических вопросов ("сравни X и Y", "найди лучший по критерию").
# Каждый hop = отдельный LLM вызов для формулировки следующего запроса.
# =============================================================================


# =============================================================================
# ШАГ 3: AGENTIC RAG — с TypedDict состоянием
#
# ЧТО ЕСТЬ: LLM-агент, управляющий процессом поиска
# ЧТО ДЕЛАЕМ: строим граф состояний (StateGraph) для Agentic RAG
# КАК РАБОТАЕТ:
#   1. query_planner: анализирует запрос, при необходимости декомпозирует
#   2. retrieval: выполняет поиск
#   3. reflection: оценивает качество найденного
#   4. if confidence < 0.5: повторный поиск с уточнённым запросом
#   5. generate: формирует финальный ответ
#   Error rate снижается на 78% vs одноразовый поиск (слайд 14)
#
# Слайд 14: «Agentic RAG: агент решает сколько раз искать»
# Слайд 15: «StateGraph: явное состояние вместо черного ящика»
# Слайд 16: «Reflection loop: агент проверяет сам себя»
# =============================================================================

try:
    from typing import TypedDict

    class AgentState(TypedDict):
        """Состояние Agentic RAG агента."""
        query: str              # текущий поисковый запрос
        original_query: str     # исходный вопрос пользователя
        search_results: list    # найденные документы
        answer: str             # финальный ответ
        confidence: float       # оценка качества найденного [0.0, 1.0]
        iteration: int          # номер текущей итерации
        max_iterations: int     # лимит итераций (защита от бесконечного цикла)
        reasoning: list[str]    # лог решений агента (для отладки)

    def query_planner(state: AgentState) -> AgentState:
        """
        Планировщик запросов: анализирует и при необходимости расширяет запрос.
        В production: LLM декомпозирует сложный вопрос на подзапросы.
        """
        reasoning = state.get("reasoning", [])
        query = state["query"]

        # Mock: если запрос очень короткий — добавляем контекст
        if len(query.split()) < 3:
            expanded = f"{query} финансовые показатели результаты 2025 2026"
            reasoning.append(f"Планировщик: запрос расширен → '{expanded}'")
            return {**state, "query": expanded, "reasoning": reasoning}

        reasoning.append(f"Планировщик: запрос принят как есть → '{query}'")
        return {**state, "reasoning": reasoning}

    def retrieval_node(state: AgentState) -> AgentState:
        """Узел поиска: выполняет векторный поиск."""
        results = vector_search(state["query"], top_k=5)
        reasoning = state.get("reasoning", [])
        reasoning.append(f"Retrieval: найдено {len(results)} документов")
        return {
            **state,
            "search_results": results,
            "iteration": state["iteration"] + 1,
            "reasoning": reasoning,
        }

    def reflection_node(state: AgentState) -> AgentState:
        """
        Рефлексия: оценивает качество найденных документов.
        В production: LLM оценивает достаточность контекста.
        Mock: confidence = средний cosine score найденных документов.
        """
        results = state["search_results"]
        reasoning = state.get("reasoning", [])

        if results:
            # Уверенность = средний score поиска (нормирован [0, 1])
            confidence = sum(r["score"] for r in results) / len(results)
        else:
            confidence = 0.0

        reasoning.append(f"Рефлексия (итерация {state['iteration']}): confidence={confidence:.2f}")

        # Если уверенность низкая — уточняем запрос для следующей итерации
        if confidence < 0.5 and results:
            # Mock: берём тикер первого результата для уточнения
            ticker = results[0]["doc"]["ticker"]
            new_query = f"{state['original_query']} {ticker} подробности"
            reasoning.append(f"Рефлексия: confidence низкий → уточняем запрос: '{new_query}'")
            return {**state, "confidence": confidence, "query": new_query, "reasoning": reasoning}

        return {**state, "confidence": confidence, "reasoning": reasoning}

    def should_retry(state: AgentState) -> str:
        """
        Условный переход: продолжить поиск или перейти к генерации?
        Возвращает строку с именем следующего узла графа.
        """
        if state["confidence"] < 0.5 and state["iteration"] < state["max_iterations"]:
            return "retry"  # → retrieval_node
        return "generate"   # → generate_node

    def generate_node(state: AgentState) -> AgentState:
        """Генерация финального ответа через Claude Haiku на основе найденного контекста."""
        results = state["search_results"]
        context_parts = [
            f"[{r['doc']['ticker']}] {r['doc']['source']} ({r['doc']['date']}):\n{r['doc']['content']}"
            for r in results[:3]
        ]
        context = "\n\n".join(context_parts)

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system="Ты финансовый аналитик. Отвечай ТОЛЬКО на основе предоставленного контекста. "
                   "Ссылайся на тикер и источник. Если информации недостаточно — скажи об этом.",
            messages=[{"role": "user", "content":
                f"Контекст:\n{context}\n\nВопрос: {state['original_query']}"}],
        )
        answer = response.content[0].text
        reasoning = state.get("reasoning", [])
        reasoning.append(f"Генерация: ответ получен от Claude Haiku ({len(results)} документов)")
        return {**state, "answer": answer, "reasoning": reasoning}

    def run_agentic_rag(query: str, max_iterations: int = 3) -> dict:
        """Запускает Agentic RAG без LangGraph (симуляция StateGraph)."""
        # Начальное состояние
        state: AgentState = {
            "query": query,
            "original_query": query,
            "search_results": [],
            "answer": "",
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": max_iterations,
            "reasoning": [],
        }

        # Шаг 1: планировщик
        state = query_planner(state)

        # Шаг 2-N: поиск → рефлексия → решение
        while state["iteration"] < max_iterations:
            state = retrieval_node(state)
            state = reflection_node(state)
            decision = should_retry(state)
            if decision == "generate":
                break

        # Финальный шаг: генерация
        state = generate_node(state)
        return state

    print("\n=== Agentic RAG (симуляция StateGraph) ===")
    result = run_agentic_rag(
        "Какие российские компании платят высокие дивиденды при низком долге?",
        max_iterations=2,
    )
    print(f"Итераций поиска: {result['iteration']}")
    print(f"Итоговый confidence: {result['confidence']:.2f}")
    print(f"Ответ: {result['answer']}")
    print("\nЛог решений агента:")
    for step in result["reasoning"]:
        print(f"  → {step}")

    print("\nСтруктура LangGraph GraphRAG:")
    print("  START → query_planner → retrieval → reflection")
    print("             ↑                              ↓ [confidence<0.5 AND iter<max]")
    print("             └─────────── retry ────────────┘")
    print("                                            ↓ [generate]")
    print("                                       generate → END")

except Exception as e:
    print(f"Agentic RAG ошибка: {e}")


# =============================================================================
# SUMMARY 2: Шаг 3
# Agentic RAG — агент сам решает сколько раз искать (до max_iterations).
# TypedDict: явная схема состояния = легче отлаживать и тестировать.
# Reflection node — ключевой: без него агент не знает когда остановиться.
# LangGraph добавляет: персистентность состояния, параллельные ветки, чекпоинты.
# =============================================================================


# =============================================================================
# ШАГ 4: GRAPHRAG — знания как граф
#
# ЧТО ЕСТЬ: плоский корпус документов
# ЧТО ДЕЛАЕМ: строим граф сущностей и их связей → ищем по графу
# КАК РАБОТАЕТ:
#   Microsoft GraphRAG (2024):
#   1. LLM извлекает сущности (компания, метрика, событие) из каждого документа
#   2. LLM определяет связи между сущностями
#   3. Поиск по графу: находим узлы → их соседей → документы
#   Comprehensiveness: +72-83% для глобальных вопросов ("сравни все компании")
#
# Слайд 18: «GraphRAG: от документов к знаниям — связи важнее текста»
# =============================================================================

def extract_entities(text: str) -> list[str]:
    """
    Извлекает финансовые сущности из текста.
    В production: LLM извлекает (компания, метрика, значение, дата) тройки.
    Mock: ищем тикеры по ключевым словам.
    """
    financial_entities = []
    ticker_keywords = {
        "SBER": ["сбербанк", "sber"],
        "GAZP": ["газпром", "gazp"],
        "YNDX": ["яндекс", "yndx"],
        "NVDA": ["nvidia", "nvda"],
        "AAPL": ["apple", "aapl"],
        "TSLA": ["tesla", "tsla"],
        "LKOH": ["лукойл", "лкох", "lkoh"],
        "MGNT": ["магнит", "mgnt"],
        "ALRS": ["алроса", "alrs"],
        "META": ["meta", "facebook"],
        "ROSN": ["роснефть", "rosn"],
        "GMKN": ["норникель", "gmkn"],
        "MSFT": ["microsoft", "msft"],
        "POSI": ["positive", "posi"],
        "OZON": ["ozon", "озон"],
    }

    text_lower = text.lower()
    for ticker, keywords in ticker_keywords.items():
        if any(kw in text_lower for kw in keywords):
            financial_entities.append(ticker)

    return financial_entities


def build_knowledge_graph(knowledge_base: list[dict]) -> dict:
    """Строит граф: graph[ticker] = {documents, sector, related}."""
    # Классификация тикеров по секторам
    sectors = {
        "банки": ["SBER"],
        "нефть_газ": ["GAZP", "LKOH", "ROSN"],
        "IT": ["YNDX", "MSFT", "META", "POSI"],
        "полупроводники": ["NVDA"],
        "ритейл": ["AAPL", "TSLA", "MGNT", "OZON"],
        "горнодобыча": ["ALRS", "GMKN"],
    }

    # Инвертируем: тикер → сектор
    ticker_to_sector = {}
    for sector, tickers in sectors.items():
        for t in tickers:
            ticker_to_sector[t] = sector

    graph: dict = {}

    for doc in knowledge_base:
        ticker = doc["ticker"]
        if ticker not in graph:
            graph[ticker] = {
                "documents": [],
                "sector": ticker_to_sector.get(ticker, "другой"),
                "related": [],  # заполним ниже
            }
        graph[ticker]["documents"].append(doc)

    # Добавляем связи: тикеры одного сектора связаны между собой
    for ticker, data in graph.items():
        sector = data["sector"]
        data["related"] = [
            t for t, d in graph.items()
            if d["sector"] == sector and t != ticker
        ]

    return graph


def graphrag_retrieve(query: str, graph: dict, top_k: int = 5) -> list[dict]:
    """
    Поиск по графу знаний.
    1. Извлекаем сущности из запроса
    2. Ищем документы напрямую для найденных сущностей
    3. Добавляем документы связанных (related) сущностей
    4. Fallback на векторный поиск если граф не помог
    """
    entities = extract_entities(query)
    results = []
    seen_tickers = set()

    print(f"  GraphRAG: найдены сущности в запросе: {entities}")

    # Документы найденных сущностей
    for entity in entities:
        if entity in graph:
            results.extend(graph[entity]["documents"])
            seen_tickers.add(entity)

    # Документы связанных сущностей (соседи в графе)
    for entity in entities:
        if entity in graph:
            for related_ticker in graph[entity]["related"][:2]:  # не более 2 соседей
                if related_ticker not in seen_tickers and related_ticker in graph:
                    results.extend(graph[related_ticker]["documents"])
                    seen_tickers.add(related_ticker)

    # Fallback: если граф не нашёл ничего — используем векторный поиск
    if not results:
        print("  GraphRAG fallback → векторный поиск")
        results = [r["doc"] for r in vector_search(query, top_k=top_k)]

    # Убираем дубликаты, ограничиваем top_k
    seen_content = set()
    unique_results = []
    for doc in results:
        key = doc["ticker"] + doc["date"]
        if key not in seen_content:
            seen_content.add(key)
            unique_results.append(doc)

    return unique_results[:top_k]


# Строим граф знаний
knowledge_graph = build_knowledge_graph(KNOWLEDGE_BASE)
print("\n=== GraphRAG ===")
print(f"Узлов в графе: {len(knowledge_graph)}")
print(f"Пример узла SBER: сектор='{knowledge_graph['SBER']['sector']}', "
      f"связан с: {knowledge_graph['SBER']['related']}")

# Запросы по графу
test_queries = [
    "дивиденды российских компаний 2025-2026",
    "сравни выручку Microsoft и Meta",
    "нефтяные компании добыча",
]

for q in test_queries:
    print(f"\nЗапрос: '{q}'")
    graph_results = graphrag_retrieve(q, knowledge_graph, top_k=4)
    tickers = [d["ticker"] for d in graph_results]
    print(f"  Найдено {len(graph_results)} документов: {tickers}")


# =============================================================================
# ЗАДАЧА (финансовый домен)
# =============================================================================
"""
ЗАДАЧА: Реализуй Agentic RAG с двумя инструментами

Запрос: "Сравни дивидендную доходность LKOH и GMKN"

Шаги:
1. Расширь AgentState: добавь tools_used: list[str] и sub_queries: list[str].

2. Реализуй два инструмента:
   - ticker_lookup(ticker: str) → dict: ищет документ по тикеру в KNOWLEDGE_BASE
   - sector_search(sector: str) → list[dict]: ищет все компании сектора через граф

3. Обнови query_planner():
   - Если "сравни" в запросе → декомпозируй в два sub_queries (по одному на тикер)
   - Запускай ticker_lookup для каждого sub_query

4. Обнови reflection_node():
   - confidence = 1.0 если найдены оба тикера
   - confidence = 0.5 если найден один тикер
   - confidence = 0.0 если ничего не найдено

5. Ожидаемый лог запуска:
   → Планировщик: sub_queries: ['LKOH дивиденды', 'GMKN дивиденды']
   → Retrieval: ticker_lookup('LKOH') → 1 документ
   → Retrieval: ticker_lookup('GMKN') → 1 документ
   → Рефлексия: confidence=1.0
   → Генерация: ответ на основе 2 документов
"""

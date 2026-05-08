"""
ФАЙЛ 1: Базовый RAG пайплайн — без LangChain, только sklearn + sentence-transformers
======================================
Документация: https://sbert.net/
Слайды: 3–12
"""

import os
import numpy as np
import anthropic
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

load_dotenv()

# =============================================================================
# ШАГ 1: БАЗА ЗНАНИЙ
#
# ЧТО ЕСТЬ: финансовые новости и аналитика по 15 эмитентам
# ЧТО ДЕЛАЕМ: формируем корпус документов для поиска
# КАК РАБОТАЕТ:
#   1. Каждый документ — словарь с тикером, датой, источником и текстом
#   2. to_text() объединяет поля в единую строку для embedding
#   3. corpus — список строк, каждая представляет один документ
#
# Слайд 3: «RAG = правильный контекст + правильная генерация»
# Слайд 4: «База знаний — источник истины для LLM»
# =============================================================================

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
    # Объединяем все поля — модель видит тикер, дату, источник и текст
    return f"[{doc['ticker']}] {doc['date']} ({doc['source']}): {doc['content']}"


# Создаём корпус строк для индексирования
corpus = [to_text(doc) for doc in KNOWLEDGE_BASE]
print(f"Корпус: {len(corpus)} документов")
print(f"Пример: {corpus[0][:80]}...")


# =============================================================================
# ШАГ 2: ВЕКТОРИЗАЦИЯ
#
# ЧТО ЕСТЬ: корпус текстов (список строк)
# ЧТО ДЕЛАЕМ: конвертируем каждый текст в числовой вектор
# КАК РАБОТАЕТ:
#   1. SentenceTransformer загружает предобученную модель
#   2. encode() прогоняет каждый текст через BERT → усредняет токены → вектор
#   3. corpus_embeddings: матрица [15, 384] — 15 документов по 384 числа
#
# Слайд 8: «Embedding = смысловые координаты текста в N-мерном пространстве»
# =============================================================================

# Многоязычная модель — понимает и русский, и английский
# Для GPU в Colab используй: Qwen/Qwen3-Embedding-0.6B (лучше для русского)
embed_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

print("\nВекторизация корпуса...")
corpus_embeddings = embed_model.encode(corpus, show_progress_bar=False)
print(f"Размер матрицы эмбеддингов: {corpus_embeddings.shape}")
# Ожидаем [15, 384] — 15 документов, 384-мерные векторы


# =============================================================================
# ШАГ 3: ПОИСК
#
# ЧТО ЕСТЬ: матрица эмбеддингов корпуса + запрос пользователя
# ЧТО ДЕЛАЕМ: ищем top-K документов наиболее близких к запросу
# КАК РАБОТАЕТ:
#   1. Кодируем запрос в вектор того же пространства
#   2. Считаем cosine_similarity между запросом и всеми документами
#   3. Сортируем по убыванию → берём top_k индексов
#
# Слайд 10: «Cosine similarity: угол между векторами = семантическое расстояние»
# =============================================================================

def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Семантический поиск в базе знаний.
    Возвращает top_k наиболее релевантных документов с их скорами.
    """
    # Кодируем запрос: shape [1, 384]
    query_vec = embed_model.encode([query])

    # Считаем cosine similarity: shape [1, 15] → берём [0] → shape [15]
    scores = cosine_similarity(query_vec, corpus_embeddings)[0]

    # argsort даёт индексы от минимума к максимуму
    # [::-1] разворачивает → от максимума к минимуму
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "idx": int(idx),
            "doc": KNOWLEDGE_BASE[idx],
            "text": corpus[idx],
            "score": float(scores[idx]),
        })
    return results


# Пример поиска
print("\n--- Поиск: дивиденды Лукойла по годам---")
results = search("дивиденды Лукойла по годам", top_k=3)
for r in results:
    print(f"  [{r['doc']['ticker']}] score={r['score']:.3f}: {r['doc']['content'][:60]}...")


# =============================================================================
# SUMMARY 1: Шаги 1-3
# Мы построили минимальный retrieval: корпус → эмбеддинги → поиск.
# База знаний: 15 финансовых документов по эмитентам РФ и США.
# Модель paraphrase-multilingual-MiniLM-L12-v2 понимает русский и английский.
# Поиск за O(N) — для 15 документов достаточно, для 100k нужен FAISS.
# =============================================================================


# =============================================================================
# ШАГ 4: ПРОМПТ И ГЕНЕРАЦИЯ
#
# ЧТО ЕСТЬ: retrieved контекст + вопрос пользователя
# ЧТО ДЕЛАЕМ: формируем промпт для LLM и получаем ответ
# КАК РАБОТАЕТ:
#   1. build_prompt() вставляет найденные документы в шаблон
#   2. LLM читает контекст и отвечает только на его основе
#   3. mock_llm() симулирует ответ (в production — Claude API)
#
# Слайд 11: «Промпт = инструкция + контекст + вопрос»
# Слайд 12: «Grounding: LLM не должен придумывать то, чего нет в контексте»
# =============================================================================

SYSTEM_PROMPT = """Ты финансовый аналитик. Отвечай только на основе предоставленного контекста.
Если информации в контексте недостаточно — скажи об этом явно.
Ссылайся на тикер и источник при каждом утверждении."""


def build_prompt(query: str, context_docs: list[dict]) -> str:
    """Формирует промпт: системный + контекст + вопрос пользователя."""
    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        d = doc["doc"]
        context_parts.append(f"[{i}] {d['ticker']} ({d['source']}, {d['date']}):\n{d['content']}")

    context_str = "\n\n".join(context_parts)

    return f"""{SYSTEM_PROMPT}

=== КОНТЕКСТ ===
{context_str}

=== ВОПРОС ===
{query}

=== ОТВЕТ ==="""


def claude_haiku(prompt: str) -> str:

    CUR_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(CUR_DIR, '.env'))

    """Вызов Claude Haiku — генерирует ответ на основе RAG-контекста."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def rag_answer(query: str, top_k: int = 5) -> str:
    """Полный RAG пайплайн: поиск → промпт → генерация."""
    # 1. Поиск релевантных документов
    retrieved = search(query, top_k=top_k)

    # 2. Формируем промпт с контекстом
    prompt = build_prompt(query, retrieved)

    # 3. Генерируем ответ через Claude Haiku
    answer = claude_haiku(prompt)

    return answer


# print("\n--- RAG Answer: ЛУКОЙЛ финансы ---")
answer = rag_answer("Какова выручка ЛУКОЙЛа в 2025 году и какие дивиденды он платит акционерам?")
print(answer)


# =============================================================================
# ШАГ 5: GOLDEN DATASET И МЕТРИКИ
#
# ЧТО ЕСТЬ: система поиска + набор тестовых вопросов с правильными ответами
# ЧТО ДЕЛАЕМ: автоматически оцениваем качество retrieval
# КАК РАБОТАЕТ:
#   1. Для каждого вопроса знаем, какой документ является правильным
#   2. Запускаем search() → смотрим, попал ли нужный документ в top-K
#   3. Hit Rate: доля вопросов с правильным документом в top-K
#   4. MRR: учитывает позицию правильного документа
#
# Слайд 30: «Hit Rate@K: попал ли правильный документ в первые K результатов?»
# Слайд 31: «MRR: чем выше правильный документ в списке — тем лучше»
# =============================================================================

# Golden dataset: 10 вопросов по разным эмитентам из KNOWLEDGE_BASE.
# Каждый вопрос однозначно указывает на один конкретный документ.
GOLDEN_DATASET = [
    {"question": "Какую долю прибыли Сбербанк направляет на дивиденды?",          "relevant_idx": 0},
    {"question": "Почему Газпром не выплачивает дивиденды за 2025 год?",           "relevant_idx": 1},
    {"question": "Какова целевая цена акций Яндекса по мнению аналитиков?",        "relevant_idx": 2},
    {"question": "Какова валовая маржа NVIDIA в Q4 FY2026?",                       "relevant_idx": 3},
    {"question": "Каков FCF ЛУКОЙЛа за 2025 год?",                                "relevant_idx": 6},
    {"question": "Какова себестоимость добычи нефти на проекте Восток Ойл?",       "relevant_idx": 10},
    {"question": "Сколько тонн никеля добыл Норникель в 2025 году?",               "relevant_idx": 11},
    {"question": "Сколько подписчиков у Microsoft Copilot?",                       "relevant_idx": 12},
    {"question": "Как выросли отгрузки Positive Technologies в 2025 году?",        "relevant_idx": 13},
    {"question": "Когда Ozon впервые показал положительный EBITDA?",               "relevant_idx": 14},
]


def calculate_metrics(top_k: int = 5) -> dict:
    """
    Считает Hit Rate и MRR на GOLDEN_DATASET.

    Hit Rate@K = доля запросов, где правильный документ вошёл в top-K
    MRR = среднее значение 1/rank для правильного документа (0 если не найден)
    """
    hits = 0
    reciprocal_ranks = []

    for item in GOLDEN_DATASET:
        results = search(item["question"], top_k=top_k)
        retrieved_indices = [r["idx"] for r in results]

        # Hit Rate: попал ли правильный документ в top-K?
        if item["relevant_idx"] in retrieved_indices:
            hits += 1
            # MRR: на какой позиции?
            rank = retrieved_indices.index(item["relevant_idx"]) + 1  # 1-based
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    total = len(GOLDEN_DATASET)
    hit_rate = hits / total
    mrr = sum(reciprocal_ranks) / total

    return {
        "hit_rate": hit_rate,
        "mrr": mrr,
        "hits": hits,
        "total": total,
        "top_k": top_k,
    }


print("\n--- Метрики качества retrieval ---")
for k in [1, 3, 5]:
    metrics = calculate_metrics(top_k=k)
    hr_ok = "OK" if metrics["hit_rate"] >= 0.85 else "НИЖЕ ПОРОГА"
    mrr_ok = "OK" if metrics["mrr"] >= 0.75 else "НИЖЕ ПОРОГА"
    print(f"top-{k}: Hit Rate={metrics['hit_rate']:.2f} [{hr_ok}] | MRR={metrics['mrr']:.3f} [{mrr_ok}]")

print("\nПороги (из слайда 38):")
print("  Hit Rate >= 0.85 | MRR >= 0.75")

'''

--- Метрики качества retrieval ---
top-1: Hit Rate=1.00 [OK] | MRR=1.000 [OK]
top-3: Hit Rate=1.00 [OK] | MRR=1.000 [OK]
top-5: Hit Rate=1.00 [OK] | MRR=1.000 [OK]

Пороги (из слайда 38):
  Hit Rate >= 0.85 | MRR >= 0.75

'''


# =============================================================================
# SUMMARY 2: Шаги 4-5
# Полный RAG цикл: корпус → векторы → поиск → промпт → генерация → оценка.
# GOLDEN_DATASET — минимум 10 вопросов на проверку retrieval.
# Hit Rate и MRR — стандартные метрики качества поиска (не генерации).
# Для оценки генерации нужны Faithfulness, Answer Relevancy (см. файл 04).
# =============================================================================


# =============================================================================
# ДОПОЛНИТЕЛЬНО: Pydantic AI output_validator — год запроса vs год данных
#
# ЧТО ЕСТЬ: RAG-пайплайн работает, retrieval находит правильные чанки.
# ПРОБЛЕМА: Hit Rate=1.0 не гарантирует корректность ответа — эмбеддинг
#   находит нужный документ по тикеру даже если в вопросе указан неверный год.
#   Пример: вопрос "FCF ЛУКОЙЛа за 2026?" → retrieval найдёт doc с 2025 →
#   LLM ответит данными за 2025, но вопрос был про 2026.
# ЧТО ДЕЛАЕМ: навешиваем output_validator поверх генерации — сравниваем
#   год из вопроса (в deps) с годом данных в ответе LLM (в FinancialAnswer).
# КАК РАБОТАЕТ:
#   1. Задаём зависимости QueryDeps (requested_year, ticker, rag_context)
#   2. LLM возвращает FinancialAnswer с полем data_year (что РЕАЛЬНО в данных)
#   3. output_validator сравнивает: requested_year == data_year
#   4. Если не совпадает → ModelRetry с явным сообщением об ошибке
#   5. LLM переформулирует или признаёт отсутствие данных за нужный год
#
# Слайд 54: Pydantic AI — structured output + runtime validation
# =============================================================================

try:
    import asyncio
    from dataclasses import dataclass
    from pydantic import BaseModel, field_validator
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.exceptions import ModelRetry

    @dataclass
    class QueryDeps:
        """Зависимости: что пользователь запросил + контекст из RAG."""
        requested_year: int
        requested_ticker: str
        rag_context: str  # ← видим что передаём в модель после retrieval

    class FinancialAnswer(BaseModel):
        """Структурированный ответ LLM — год указывает LLM из данных контекста."""
        ticker: str
        data_year: int     # ← LLM указывает год данных ИЗ КОНТЕКСТА (не из вопроса)
        value: str         # ← числовое значение метрики
        answer: str        # ← полный текстовый ответ

    financial_agent = Agent(
        "anthropic:claude-haiku-4-5-20251001",
        deps_type=QueryDeps,
        output_type=FinancialAnswer,
        system_prompt=(
            "Ты финансовый аналитик. Отвечай СТРОГО на основе предоставленного контекста. "
            "В поле data_year укажи год данных ИЗ КОНТЕКСТА (не из вопроса пользователя). "
            "Если в контексте нет данных за запрошенный год — укажи реальный год из контекста "
            "и в поле answer объясни это явно."
        ),
    )

    @financial_agent.output_validator
    async def validate_year_match(ctx: RunContext[QueryDeps], output: FinancialAnswer) -> FinancialAnswer:
        """
        Проверяем: год в вопросе совпадает с годом данных в ответе.
        Если нет → ModelRetry — LLM должна явно сообщить о несовпадении.
        """
        if output.data_year != ctx.deps.requested_year:
            # Год не совпал — проверяем, признала ли LLM это в ответе
            if str(ctx.deps.requested_year) not in output.answer:
                raise ModelRetry(
                    f"Несоответствие года: вопрос за {ctx.deps.requested_year}, "
                    f"но контекст содержит данные за {output.data_year}. "
                    f"Укажи в поле answer, что данных за {ctx.deps.requested_year} нет, "
                    f"и предоставь данные за {output.data_year}."
                )
        return output

    # Тестовые вопросы: ✓ правильный год, ✗ неверный год
    DEMO_QUESTIONS = [
        {"q": "Каков FCF ЛУКОЙЛа за 2025 год?",           "year": 2025, "ticker": "LKOH"},  # ✓ год верный
        {"q": "Каков FCF ЛУКОЙЛа за 2026 год?",           "year": 2026, "ticker": "LKOH"},  # ✗ данных нет
        {"q": "Какую прибыль показал Сбербанк за 2025?",   "year": 2025, "ticker": "SBER"},  # ✓ год верный
        {"q": "Сколько дивидендов Норникель выплатил в 2024 году?", "year": 2024, "ticker": "GMKN"},  # ✗ данных нет
    ]

    async def run_year_validation_demo():
        print("\n" + "="*70)
        print("ДОПОЛНИТЕЛЬНО: Pydantic AI output_validator — год запроса vs год данных")
        print("="*70)

        for item in DEMO_QUESTIONS:
            print(f"\n{'─'*60}")
            print(f"ВОПРОС: {item['q']}")
            print(f"Запрошен год: {item['year']} | Тикер: {item['ticker']}")

            # --- Retrieval: ищем релевантные чанки из KNOWLEDGE_BASE ---
            q_vec = embed_model.encode([item["q"]])
            scores = cosine_similarity(q_vec, corpus_embeddings)[0]
            top_idx = int(np.argmax(scores))
            retrieved_doc = corpus[top_idx]  # строка, а не словарь

            print(f"\n[RAG] Извлечённый документ (idx={top_idx}):")
            print(f"  {retrieved_doc[:120]}...")

            # --- Передаём контекст в модель через QueryDeps ---
            deps = QueryDeps(
                requested_year=item["year"],
                requested_ticker=item["ticker"],
                rag_context=retrieved_doc,
            )

            prompt = (
                f"Контекст из базы знаний:\n{retrieved_doc}\n\n"
                f"Вопрос: {item['q']}\n\n"
                f"Ответь структурированно. В data_year укажи год данных из контекста."
            )

            print(f"\n[ПРОМПТ → модель]:\n  Контекст: {retrieved_doc[:80]}...")
            print(f"  Запрошенный год в deps: {deps.requested_year}")

            try:
                result = await financial_agent.run(prompt, deps=deps)
                out = result.output
                year_ok = out.data_year == item["year"]
                status = "✓ ГОД СОВПАЛ" if year_ok else "⚠ ПРИНЯТ (честный ответ о несовпадении)"
                print(f"\n[ОТВЕТ] {status}")
                print(f"  ticker:    {out.ticker}")
                print(f"  data_year: {out.data_year}  (запрошен: {item['year']})")
                print(f"  value:     {out.value}")
                print(f"  answer:    {out.answer[:200]}")
            except Exception as e:
                print(f"\n[ОШИБКА после retries]: {type(e).__name__}: {e}")

    # Запуск демо
    asyncio.run(run_year_validation_demo())

except ImportError as e:
    print(f"\n[ДОПОЛНИТЕЛЬНО пропущено] pydantic-ai не установлен: {e}")
    print("Установи: pip install pydantic-ai")
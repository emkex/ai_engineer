"""
ФАЙЛ 4: Полная система оценки RAG — все 12 метрик из презентации
======================================
Документация: https://github.com/explodinggradients/ragas
Слайды: 27–38, 45, 53
"""

import os
import math
import numpy as np
import pandas as pd
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

# Загружаем модель и строим индекс
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("Векторизация корпуса...")
corpus_embeddings = embed_model.encode(corpus, show_progress_bar=False)


def search(query: str, top_k: int = 5) -> list[dict]:
    """Базовый векторный поиск — используется во всех метриках."""
    query_vec = embed_model.encode([query])
    scores = cosine_similarity(query_vec, corpus_embeddings)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [
        {"idx": int(i), "doc": KNOWLEDGE_BASE[i], "score": float(scores[i])}
        for i in top_indices
    ]


# =============================================================================
# ШАГ 1: GOLDEN DATASET
#
# ЧТО ЕСТЬ: RAG система с базой знаний из 15 документов
# ЧТО ДЕЛАЕМ: создаём эталонный набор Q&A для автоматической оценки
# КАК РАБОТАЕТ:
#   1. Для каждого вопроса знаем правильный ответ (ground_truth)
#   2. Знаем, какой документ содержит ответ (relevant_idx)
#   3. Знаем, какие фрагменты текста должны быть в контексте (contexts)
#
# Слайд 27: «Golden Dataset — фундамент оценки RAG»
# Слайд 29: «Без golden dataset невозможно измерить качество системы»
# =============================================================================

GOLDEN_DATASET = [
    {
        "question": "Какова чистая прибыль Сбербанка за Q1 2026?",
        "ground_truth_answer": "432 млрд рублей",
        "relevant_idx": 0,
        "contexts": ["чистая прибыль Q1 2026 = 432 млрд руб (+18% г/г)"],
    },
    {
        "question": "Почему Газпром не платит дивиденды?",
        "ground_truth_answer": "Высокая долговая нагрузка: ND/EBITDA=3.1x, падение выручки -12%",
        "relevant_idx": 1,
        "contexts": ["Дивиденды не рекомендованы. ND/EBITDA=3.1x"],
    },
    {
        "question": "Каков прогноз выручки Яндекса в 2026 году?",
        "ground_truth_answer": "+35-40%",
        "relevant_idx": 2,
        "contexts": ["Прогноз 2026: +35-40%"],
    },
    {
        "question": "Какова валовая маржа NVIDIA в Q4 FY2026?",
        "ground_truth_answer": "73.5%",
        "relevant_idx": 3,
        "contexts": ["Gross margin 73.5%"],
    },
    {
        "question": "Какие дивиденды платит Apple на акцию?",
        "ground_truth_answer": "$0.25 на акцию",
        "relevant_idx": 4,
        "contexts": ["Dividend $0.25/share"],
    },
    {
        "question": "Сколько алмазов добудет АЛРОСА в 2026 году?",
        "ground_truth_answer": "34.5 млн карат",
        "relevant_idx": 8,
        "contexts": ["Прогноз добычи 2026: 34.5 млн карат"],
    },
    {
        "question": "Каков GMV Ozon в 2025 году?",
        "ground_truth_answer": "3.1 трлн рублей",
        "relevant_idx": 14,
        "contexts": ["GMV 3.1 трлн руб (+62%)"],
    },
    {
        "question": "Какие дивиденды выплачивает Норникель?",
        "ground_truth_answer": "1400 рублей на акцию",
        "relevant_idx": 11,
        "contexts": ["Дивиденды: 1400 руб/акция"],
    },
    {
        "question": "Каков объём добычи нефти Роснефти на Восток Ойл?",
        "ground_truth_answer": "500 тысяч баррелей в сутки",
        "relevant_idx": 10,
        "contexts": ["Добыча: 500 тыс баррелей/сутки"],
    },
    {
        "question": "Сколько подписчиков у Microsoft Copilot?",
        "ground_truth_answer": "45 миллионов",
        "relevant_idx": 12,
        "contexts": ["Copilot: 45M subscribers"],
    },
    {
        "question": "Какой buyback объявил ЛУКОЙЛ?",
        "ground_truth_answer": "25 млрд рублей",
        "relevant_idx": 6,
        "contexts": ["Buyback 25 млрд"],
    },
    {
        "question": "Каков рост отгрузок Positive Technologies в 2025 году?",
        "ground_truth_answer": "+35%",
        "relevant_idx": 13,
        "contexts": ["отгрузки 32 млрд руб (+35%)"],
    },
]

print(f"\nGolden Dataset: {len(GOLDEN_DATASET)} вопросов")


# =============================================================================
# ШАГ 2: RETRIEVAL МЕТРИКИ
#
# ЧТО ЕСТЬ: golden dataset + функция поиска
# ЧТО ДЕЛАЕМ: считаем три стандартные retrieval метрики
# КАК РАБОТАЕТ:
#   Hit Rate: бинарная метрика — попал/не попал
#   MRR: учитывает позицию (rank 1 лучше чем rank 5)
#   NDCG: обобщение MRR с логарифмическим дисконтом позиции
#
# Слайд 30: «Hit Rate@K — самая простая метрика: попал ли в top-K?»
# Слайд 31: «MRR — учитывает позицию правильного документа»
# Слайд 32: «NDCG — стандарт в задачах Information Retrieval»
# =============================================================================

def hit_rate_at_k(dataset: list[dict], search_fn, k: int = 5) -> float:
    """
    Hit Rate@K = |{q: relevant в top-K}| / |Q|

    Слайд 30: бинарная метрика качества retrieval.
    Порог: >= 0.85
    """
    hits = 0
    for item in dataset:
        results = search_fn(item["question"], top_k=k)
        retrieved_indices = [r["idx"] for r in results]
        if item["relevant_idx"] in retrieved_indices:
            hits += 1
    return hits / len(dataset)


def mrr(dataset: list[dict], search_fn, k: int = 10) -> float:
    """
    MRR = (1/|Q|) * Σ(1/rank_i)  если документ найден, иначе 0

    Слайд 31: Mean Reciprocal Rank — штрафует за низкую позицию.
    Порог: >= 0.75
    """
    total_rr = 0.0
    for item in dataset:
        results = search_fn(item["question"], top_k=k)
        retrieved_indices = [r["idx"] for r in results]
        if item["relevant_idx"] in retrieved_indices:
            rank = retrieved_indices.index(item["relevant_idx"]) + 1  # 1-based
            total_rr += 1.0 / rank
        # Если не найден: rank = ∞ → 1/rank = 0 → ничего не добавляем
    return total_rr / len(dataset)


def ndcg_at_k(dataset: list[dict], search_fn, k: int = 5) -> float:
    """
    NDCG@K = DCG / IDCG
    DCG = Σ rel_i / log2(i+1)  для i=1..K
    IDCG = DCG идеального ранжирования (правильный документ на позиции 1)

    Для бинарной релевантности: rel=1 если idx == relevant_idx, иначе 0
    Слайд 32: NDCG нормирован [0, 1], 1.0 = идеальный результат.
    Порог: >= 0.70
    """
    total_ndcg = 0.0
    for item in dataset:
        results = search_fn(item["question"], top_k=k)
        retrieved_indices = [r["idx"] for r in results]

        # DCG: сумма релевантностей с логарифмическим дисконтом
        dcg = 0.0
        for i, idx in enumerate(retrieved_indices, start=1):
            rel = 1.0 if idx == item["relevant_idx"] else 0.0
            dcg += rel / math.log2(i + 1)

        # IDCG: идеальный DCG — правильный документ на позиции 1
        idcg = 1.0 / math.log2(2)  # = 1.0

        total_ndcg += dcg / idcg

    return total_ndcg / len(dataset)


print("\n=== Retrieval метрики ===")
for k in [1, 3, 5]:
    hr = hit_rate_at_k(GOLDEN_DATASET, search, k=k)
    m = mrr(GOLDEN_DATASET, search, k=k)
    nd = ndcg_at_k(GOLDEN_DATASET, search, k=k)
    print(f"K={k}: Hit Rate={hr:.2f} | MRR={m:.3f} | NDCG={nd:.3f}")


# =============================================================================
# SUMMARY 1: Шаги 1-2
# Golden Dataset — основа: без него нельзя измерить качество.
# Hit Rate: "нашли ли вообще?" — самая понятная метрика для бизнеса.
# MRR: "насколько высоко нашли?" — важно когда LLM читает только top-1.
# NDCG: обобщение MRR, стандарт академических исследований.
# Все три нужны: одна метрика не даёт полной картины.
# =============================================================================


# =============================================================================
# ШАГ 3: GENERATION МЕТРИКИ через LLM-as-judge
#
# ЧТО ЕСТЬ: ответ LLM + контекст + вопрос
# ЧТО ДЕЛАЕМ: автоматически оцениваем качество генерации
# КАК РАБОТАЕТ:
#   В production: RAGAS использует LLM-судью (GPT-4, Claude)
#   Здесь: упрощённые реализации через keyword overlap
#
# Слайд 33: «Faithfulness — нет ли галлюцинаций?»
# Слайд 34: «Answer Relevancy — отвечает ли на вопрос?»
# Слайд 36: «Context Precision/Recall — правильные ли документы нашли?»
# =============================================================================

def faithfulness_score(answer: str, contexts: list[str]) -> float:
    """
    Faithfulness через Claude Haiku как LLM-судья.

    Слайд 33: все утверждения ответа должны быть подтверждены контекстом.
    Порог: >= 0.85. Галлюцинация = утверждение без опоры в контексте.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    context_text = "\n".join(contexts)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content":
            f"Оцени Faithfulness ответа от 0.0 до 1.0.\n"
            f"Faithfulness = доля утверждений ответа, подтверждённых контекстом.\n\n"
            f"Контекст:\n{context_text}\n\n"
            f"Ответ:\n{answer}\n\n"
            f"Ответь ТОЛЬКО числом от 0.0 до 1.0 (например: 0.85):"}],
    )
    try:
        return float(response.content[0].text.strip())
    except ValueError:
        return 0.5


def answer_relevancy_score(answer: str, question: str) -> float:
    """
    Answer Relevancy через Claude Haiku как LLM-судья.

    Слайд 34: отвечает ли ответ именно на заданный вопрос?
    Порог: >= 0.80. Нерелевантный ответ = ответил на другой вопрос.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content":
            f"Оцени Answer Relevancy от 0.0 до 1.0.\n"
            f"Answer Relevancy = насколько ответ отвечает именно на заданный вопрос.\n\n"
            f"Вопрос: {question}\n"
            f"Ответ: {answer}\n\n"
            f"Ответь ТОЛЬКО числом от 0.0 до 1.0 (например: 0.90):"}],
    )
    try:
        return float(response.content[0].text.strip())
    except ValueError:
        return 0.5


def context_precision(retrieved_docs: list[dict], relevant_idx: int) -> float:
    """
    Context Precision = |релевантных в выдаче| / |всего в выдаче|

    Слайд 36: какой процент найденных документов действительно релевантен?
    Порог: >= 0.70
    """
    if not retrieved_docs:
        return 0.0
    relevant_found = sum(1 for d in retrieved_docs if d.get("idx") == relevant_idx)
    return relevant_found / len(retrieved_docs)


def context_recall(retrieved_docs: list[dict], relevant_idx: int) -> float:
    """Слайд 36: 1.0 если нужный документ найден, 0.0 если нет. Порог: >= 0.80"""
    return 1.0 if any(d.get("idx") == relevant_idx for d in retrieved_docs) else 0.0


def context_f1(prec: float, rec: float) -> float:
    """Context F1 = 2*P*R / (P+R). Порог: >= 0.75"""
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


# Демонстрация generation метрик на примерах
print("\n=== Generation метрики (mock реализации) ===")

test_cases = [
    {
        "question": "Какова чистая прибыль Сбербанка?",
        "answer": "Чистая прибыль Сбербанка за Q1 2026 составила 432 млрд рублей, рост +18% г/г.",
        "contexts": [KNOWLEDGE_BASE[0]["content"]],
        "relevant_idx": 0,
    },
    {
        "question": "Сколько алмазов добудет АЛРОСА?",
        "answer": "АЛРОСА планирует добыть 34.5 миллиона карат в 2026 году.",
        "contexts": [KNOWLEDGE_BASE[8]["content"]],
        "relevant_idx": 8,
    },
]

for tc in test_cases:
    retrieved = search(tc["question"], top_k=5)
    prec = context_precision(retrieved, tc["relevant_idx"])
    rec = context_recall(retrieved, tc["relevant_idx"])
    f1 = context_f1(prec, rec)
    faith = faithfulness_score(tc["answer"], tc["contexts"])
    rel = answer_relevancy_score(tc["answer"], tc["question"])

    print(f"\nВопрос: '{tc['question']}'")
    print(f"  Faithfulness:      {faith:.2f} (порог >= 0.85)")
    print(f"  Answer Relevancy:  {rel:.2f} (порог >= 0.80)")
    print(f"  Context Precision: {prec:.2f} (порог >= 0.70)")
    print(f"  Context Recall:    {rec:.2f} (порог >= 0.80)")
    print(f"  Context F1:        {f1:.2f} (порог >= 0.75)")


# =============================================================================
# SUMMARY 2: Шаг 3
# Faithfulness измеряет галлюцинации: ответ должен опираться только на контекст.
# Answer Relevancy: ответ должен отвечать именно на заданный вопрос.
# Context Precision/Recall: retrieval метрики с точки зрения LLM генерации.
# В production: LLM-as-judge (GPT-4o, Claude Opus) дает точнее mock-реализаций.
# =============================================================================


# =============================================================================
# ШАГ 4: RAGAS ДЕМОНСТРАЦИЯ
#
# ЧТО ЕСТЬ: стандартный фреймворк для оценки RAG
# ЧТО ДЕЛАЕМ: показываем как подключить ragas к нашему пайплайну
# КАК РАБОТАЕТ:
#   ragas.evaluate() принимает Dataset (HuggingFace format) → возвращает метрики
#   Внутри использует LLM-судью для точной оценки Faithfulness и Relevancy
#
# Слайд 53: «RAGAS — де-факто стандарт eval RAG в 2025-2026»
# =============================================================================

from ragas import evaluate
from ragas.metrics.collections import (
    Faithfulness,          # Верность: ответ опирается только на контекст (0..1)
    AnswerRelevancy,       # Релевантность ответа вопросу (0..1)
    ContextPrecision,      # Доля релевантных чанков среди всех извлечённых (0..1)
    ContextRecall,         # Покрытие ground_truth извлечёнными чанками (0..1)
    FactualCorrectness,    # Фактическая точность относительно ground_truth (0..1)
    AnswerCorrectness,     # Итоговая корректность = factual + semantic (0..1)
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings
from datasets import Dataset

# --- LLM-судья: Claude Haiku (не OpenAI, не Mistral) ---
haiku_judge = LangchainLLMWrapper(ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
))
# Эмбеддинги нужны для AnswerRelevancy (семантическое сравнение)
oai_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(
    api_key=os.environ.get("OPENAI_API_KEY", ""),
))

# Инициализируем метрики с нашим судьёй
metrics = [
    Faithfulness(llm=haiku_judge),
    AnswerRelevancy(llm=haiku_judge, embeddings=oai_embeddings),
    ContextPrecision(llm=haiku_judge),
    ContextRecall(llm=haiku_judge),
    FactualCorrectness(llm=haiku_judge),
    AnswerCorrectness(llm=haiku_judge, embeddings=oai_embeddings),
]

# Что означает каждая метрика — справочник
METRIC_DESCRIPTIONS = {
    "faithfulness":         ("Верность контексту",    "ответ не содержит фактов вне предоставленного контекста",         "≥ 0.85"),
    "answer_relevancy":     ("Релевантность ответа",  "ответ отвечает именно на заданный вопрос, без лишнего",           "≥ 0.80"),
    "context_precision":    ("Точность контекста",    "среди извлечённых чанков большинство действительно нужны",        "≥ 0.70"),
    "context_recall":       ("Полнота контекста",     "извлечённые чанки покрывают всё необходимое для ground_truth",    "≥ 0.80"),
    "factual_correctness":  ("Фактическая точность",  "ключевые факты в ответе совпадают с ground_truth",                "≥ 0.75"),
    "answer_correctness":   ("Корректность ответа",   "итоговая оценка: factual + семантическое сходство с ground_truth","≥ 0.75"),
}

# Датасет: 3 примера (хороший, средний, плохой контекст)
ragas_data = {
    "question": [
        "Какова чистая прибыль Сбербанка за Q1 2026?",
        "Каков FCF ЛУКОЙЛа за 2025 год?",
        "Какова валовая маржа NVIDIA в Q4 FY2026?",
    ],
    "answer": [
        "Чистая прибыль Сбербанка за Q1 2026 составила 432 млрд рублей, что на 18% выше по сравнению с аналогичным периодом прошлого года.",
        "Свободный денежный поток ЛУКОЙЛа за 2025 год составил 950 млрд рублей.",
        "Валовая маржа NVIDIA в Q4 FY2026 составила 73.5%, что отражает высокую долю Data Center сегмента.",
    ],
    "contexts": [
        ["Сбербанк: чистая прибыль Q1 2026 = 432 млрд руб (+18% г/г). NIM=5.8%. Дивиденды: 50% от прибыли МСФО. Целевая цена аналитиков: 380 руб."],
        ["ЛУКОЙЛ 2025: выручка 9.1 трлн руб (-5%). EBITDA 1.8 трлн. FCF 950 млрд. Дивиденды: 1100 руб/акция. ND/EBITDA=0.1x. Buyback 25 млрд."],
        ["NVIDIA Q4 FY2026: revenue $39.3B (+78% YoY). Data Center: $35.6B. Gross margin 73.5%. EPS $0.89. Next quarter guidance $43B. Analyst target $1200."],
    ],
    "ground_truth": [
        "432 млрд руб (+18% г/г)",
        "950 млрд руб",
        "73.5%",
    ],
}

dataset = Dataset.from_dict(ragas_data)

print("\n" + "="*65)
print("RAGAS: оценка RAG-пайплайна через LLM-судью (Claude Haiku)")
print("="*65)
print("\nЧто оцениваем:")
for key, (name, desc, threshold) in METRIC_DESCRIPTIONS.items():
    print(f"  {name:<25} — {desc}")
    print(f"  {'':25}   порог: {threshold}")

print("\nЗапускаем evaluate()... (каждый вопрос × каждая метрика = LLM-вызов)")

result = evaluate(dataset, metrics=metrics)

print("\n--- Результаты по каждой метрике ---")
scores = result.to_pandas()
for col in scores.columns:
    if col in METRIC_DESCRIPTIONS:
        name, desc, threshold = METRIC_DESCRIPTIONS[col]
        vals = scores[col].tolist()
        avg = sum(vals) / len(vals)
        ok = "OK" if avg >= float(threshold.replace("≥ ", "")) else "НИЖЕ ПОРОГА"
        print(f"\n{name} ({col})")
        print(f"  Описание: {desc}")
        print(f"  Порог:    {threshold}  →  среднее: {avg:.3f}  [{ok}]")
        for i, v in enumerate(vals):
            q_short = ragas_data["question"][i][:45]
            print(f"  Q{i+1}: {v:.3f}  «{q_short}»")

print("\n--- Детальный датафрейм ---")
print(scores[["question"] + [c for c in scores.columns if c in METRIC_DESCRIPTIONS]].to_string(index=False))


# =============================================================================
# ШАГ 5: СВОДНАЯ ТАБЛИЦА ПОРОГОВЫХ ЗНАЧЕНИЙ
#
# ЧТО ЕСТЬ: все 12 метрик с порогами из презентации
# ЧТО ДЕЛАЕМ: выводим через pandas DataFrame для удобного просмотра
# КАК РАБОТАЕТ:
#   Таблица служит чек-листом при разработке и деплое RAG
#   Каждая метрика — критерий приёмки для production
#
# Слайд 38: «Пороговые значения — критерии приёмки production системы»
# =============================================================================

metrics_reference = [
    {"метрика": "Hit Rate@K",        "порог": "≥ 0.85", "тип": "Retrieval",   "инструмент": "ручная реализация"},
    {"метрика": "MRR",               "порог": "≥ 0.75", "тип": "Retrieval",   "инструмент": "ручная реализация"},
    {"метрика": "NDCG@K",            "порог": "≥ 0.70", "тип": "Retrieval",   "инструмент": "ручная реализация"},
    {"метрика": "Faithfulness",      "порог": "≥ 0.85", "тип": "Generation",  "инструмент": "RAGAS"},
    {"метрика": "Answer Relevancy",  "порог": "≥ 0.80", "тип": "Generation",  "инструмент": "RAGAS"},
    {"метрика": "Answer Correctness","порог": "≥ 0.75", "тип": "Generation",  "инструмент": "RAGAS"},
    {"метрика": "Toxicity",          "порог": "≤ 0.05", "тип": "Safety",      "инструмент": "Detoxify"},
    {"метрика": "Context Precision", "порог": "≥ 0.70", "тип": "End-to-End",  "инструмент": "RAGAS"},
    {"метрика": "Context Recall",    "порог": "≥ 0.80", "тип": "End-to-End",  "инструмент": "RAGAS"},
    {"метрика": "Context F1",        "порог": "≥ 0.75", "тип": "End-to-End",  "инструмент": "2*P*R/(P+R)"},
    {"метрика": "Noise Robustness",  "порог": "≥ 0.90", "тип": "End-to-End",  "инструмент": "LLM-as-judge"},
    {"метрика": "Latency P95",       "порог": "< 3s",   "тип": "Performance", "инструмент": "OpenTelemetry"},
]

df = pd.DataFrame(metrics_reference)
print("\n=== Сводная таблица метрик RAG (Слайд 38) ===")
print(df.to_string(index=False))

# Считаем итоговые метрики на нашей системе
print("\n=== Итоговая оценка нашей RAG системы ===")
hr5 = hit_rate_at_k(GOLDEN_DATASET, search, k=5)
mrr5 = mrr(GOLDEN_DATASET, search, k=5)
ndcg5 = ndcg_at_k(GOLDEN_DATASET, search, k=5)

results_summary = [
    {"метрика": "Hit Rate@5",  "значение": f"{hr5:.2f}",  "порог": "≥ 0.85", "статус": "OK" if hr5 >= 0.85 else "НИЖЕ ПОРОГА"},
    {"метрика": "MRR@5",       "значение": f"{mrr5:.3f}", "порог": "≥ 0.75", "статус": "OK" if mrr5 >= 0.75 else "НИЖЕ ПОРОГА"},
    {"метрика": "NDCG@5",      "значение": f"{ndcg5:.3f}","порог": "≥ 0.70", "статус": "OK" if ndcg5 >= 0.70 else "НИЖЕ ПОРОГА"},
]
print(pd.DataFrame(results_summary).to_string(index=False))

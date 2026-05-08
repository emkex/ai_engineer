"""
ФАЙЛ 2: Гибридный поиск — BM25 + Vector + RRF + Cross-encoder reranking
======================================
Документация: https://github.com/dorianbrown/rank_bm25
Слайды: 10–11, 21
"""

import os
import numpy as np
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
    """Преобразует документ в строку для поиска."""
    return f"[{doc['ticker']}] {doc['date']} ({doc['source']}): {doc['content']}"


corpus = [to_text(doc) for doc in KNOWLEDGE_BASE]


# =============================================================================
# ШАГ 1: BM25 ПОИСК
#
# ЧТО ЕСТЬ: текстовый корпус финансовых документов
# ЧТО ДЕЛАЕМ: индексируем через BM25Okapi — статистический поиск по словам
# КАК РАБОТАЕТ:
#   1. Токенизируем каждый документ (разбиваем на слова нижнего регистра)
#   2. BM25 считает TF-IDF с насыщением (k1=1.5, b=0.75 по умолчанию)
#   3. Для запроса: считаем сумму BM25 скоров по каждому слову запроса
#
# Слайд 10: «BM25 хорошо находит документы по точным ключевым словам (тикеры, числа)»
# =============================================================================

try:
    from rank_bm25 import BM25Okapi

    def tokenize(text: str) -> list[str]:
        """Простая токенизация: нижний регистр + разбивка по пробелам."""
        # Убираем знаки препинания грубо через замену
        for ch in "[]().,!?:;\"'":
            text = text.replace(ch, " ")
        return [w for w in text.lower().split() if len(w) > 1]

    # Токенизируем весь корпус
    tokenized_corpus = [tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    def bm25_search(query: str, top_k: int = 50) -> list[tuple[int, float]]:
        """
        BM25 поиск по корпусу.
        Возвращает список (индекс_документа, bm25_score).
        """
        query_tokens = tokenize(query)
        scores = bm25.get_scores(query_tokens)

        # Сортируем по убыванию score
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in sorted_indices if scores[idx] > 0]

    print("BM25 индекс построен")
    print(f"Пример BM25 поиска 'дивиденды Сбербанк':")
    bm25_results = bm25_search("дивиденды Сбербанк", top_k=3)
    for idx, score in bm25_results:
        print(f"  [{KNOWLEDGE_BASE[idx]['ticker']}] score={score:.2f}: {KNOWLEDGE_BASE[idx]['content'][:50]}...")

except ImportError:
    print("Установи rank_bm25: pip install rank-bm25")
    # Заглушка для BM25 — возвращает пустой список
    def bm25_search(query: str, top_k: int = 50) -> list[tuple[int, float]]:
        """Заглушка BM25 (rank_bm25 не установлен)."""
        return []


# =============================================================================
# ШАГ 2: VECTOR ПОИСК
#
# ЧТО ЕСТЬ: корпус документов + мультиязычная embedding-модель
# ЧТО ДЕЛАЕМ: индексируем корпус векторами, ищем по косинусному сходству
# КАК РАБОТАЕТ:
#   1. Каждый документ → вектор 384 измерений
#   2. Запрос → вектор того же пространства
#   3. cosine_similarity → top-K ближайших документов
#
# Слайд 8-9: «Vector search хорошо находит семантически близкие документы»
# =============================================================================

# Многоязычная модель — работает с русским и английским
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

print("\nВекторизация корпуса...")
corpus_embeddings = embed_model.encode(corpus, show_progress_bar=False)


def vector_search(query: str, top_k: int = 50) -> list[tuple[int, float]]:
    """
    Векторный поиск по cosine similarity.
    Возвращает список (индекс_документа, cosine_score).
    """
    query_vec = embed_model.encode([query])
    scores = cosine_similarity(query_vec, corpus_embeddings)[0]
    sorted_indices = np.argsort(scores)[::-1][:top_k]
    return [(int(idx), float(scores[idx])) for idx in sorted_indices]


print("\nПример vector поиска 'дивидендная доходность российских акций':")
vec_results = vector_search("дивидендная доходность российских акций", top_k=3)
for idx, score in vec_results:
    print(f"  [{KNOWLEDGE_BASE[idx]['ticker']}] score={score:.3f}: {KNOWLEDGE_BASE[idx]['content'][:50]}...")


# =============================================================================
# ШАГ 3: RRF СЛИЯНИЕ
#
# ЧТО ЕСТЬ: два ранжированных списка (BM25 и Vector)
# ЧТО ДЕЛАЕМ: объединяем их через Reciprocal Rank Fusion
# КАК РАБОТАЕТ:
#   Формула RRF: score(d) = Σ 1/(k + rank(d))  где k=60 (стандартное значение)
#   - k=60 выбран эмпирически: сглаживает влияние топовых позиций
#   - Документ в топе обоих списков получает 1/(60+1) + 1/(60+1) ≈ 0.033
#   - Документ на 50-м месте получает 1/(60+50) ≈ 0.009
#
# Слайд 10: «RRF не требует нормализации скоров — работает с любыми шкалами»
# =============================================================================

def rrf_fusion(
    bm25_results: list[tuple[int, float]],
    vector_results: list[tuple[int, float]],
    k: int = 60,
) -> list[tuple[int, float]]:
    """
    Reciprocal Rank Fusion двух ранжированных списков.
    Возвращает объединённый список (индекс, rrf_score) по убыванию.
    """
    rrf_scores: dict[int, float] = {}

    # Добавляем вклад BM25
    for rank, (doc_idx, _score) in enumerate(bm25_results, start=1):
        rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + 1.0 / (k + rank)

    # Добавляем вклад Vector
    for rank, (doc_idx, _score) in enumerate(vector_results, start=1):
        rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + 1.0 / (k + rank)

    # Сортируем по убыванию RRF score
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


print("\nRRF слияние BM25 + Vector:")
bm25_all = bm25_search("дивиденды российских компаний", top_k=15)
vec_all = vector_search("дивиденды российских компаний", top_k=15)
rrf_results = rrf_fusion(bm25_all, vec_all)
print("Top-3 по RRF:")
for idx, score in rrf_results[:3]:
    print(f"  [{KNOWLEDGE_BASE[idx]['ticker']}] rrf={score:.4f}: {KNOWLEDGE_BASE[idx]['content'][:50]}...")


# =============================================================================
# SUMMARY 1: Шаги 1-3
# BM25 находит точные совпадения (тикеры, числа, специфическая терминология).
# Vector search находит семантически близкие документы (синонимы, парафразы).
# RRF объединяет оба метода без настройки весов — ключевое преимущество.
# k=60 — стандартный гиперпараметр, проверенный на множестве датасетов.
# =============================================================================


# =============================================================================
# ШАГ 4: CROSS-ENCODER РЕРАНКИНГ
#
# ЧТО ЕСТЬ: top-20 кандидатов от RRF
# ЧТО ДЕЛАЕМ: применяем точную модель для финального ранжирования
# КАК РАБОТАЕТ:
#   Bi-encoder: query → вектор, doc → вектор → независимо (быстро)
#   Cross-encoder: (query, doc) → одна модель → score (медленно, точно)
#   Pipeline: top-50 bi-encoder → top-5 cross-encoder = баланс скорости и точности
#
# Слайд 11: «Cross-encoder видит взаимодействие query и doc одновременно»
# Слайд 21: «Multi-stage Reranking: сначала широко, потом точно»
# =============================================================================

try:
    from sentence_transformers import CrossEncoder

    # Модель обучена на MS MARCO — задача passage ranking
    # Для русского языка лучше: Qwen/Qwen3-Reranker-0.6B
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(query: str, candidate_indices: list[int], top_k: int = 5) -> list[dict]:
        """
        Cross-encoder реранкинг кандидатов.
        Принимает индексы кандидатов, возвращает top_k с точными scores.
        """
        if not candidate_indices:
            return []

        # Формируем пары (query, doc) для cross-encoder
        candidate_texts = [corpus[idx] for idx in candidate_indices]
        pairs = [(query, text) for text in candidate_texts]

        # Cross-encoder выдаёт score для каждой пары
        scores = reranker.predict(pairs)

        # Объединяем индексы со скорами и сортируем
        ranked = sorted(
            zip(candidate_indices, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for idx, score in ranked[:top_k]:
            results.append({
                "idx": idx,
                "doc": KNOWLEDGE_BASE[idx],
                "text": corpus[idx],
                "score": float(score),
            })
        return results

    _has_crossencoder = True
    print("\nCross-encoder загружен")

except ImportError:
    _has_crossencoder = False
    def rerank(query: str, candidate_indices: list[int], top_k: int = 5) -> list[dict]:
        """Заглушка реранкинга (sentence_transformers не установлен)."""
        results = []
        for idx in candidate_indices[:top_k]:
            results.append({
                "idx": idx,
                "doc": KNOWLEDGE_BASE[idx],
                "text": corpus[idx],
                "score": 0.0,
            })
        return results
    print("Cross-encoder недоступен — используется заглушка")


# =============================================================================
# ШАГ 5: ПОЛНЫЙ ГИБРИДНЫЙ ПАЙПЛАЙН
#
# ЧТО ЕСТЬ: BM25 + Vector + RRF + Cross-encoder
# ЧТО ДЕЛАЕМ: собираем все шаги в единую функцию
# КАК РАБОТАЕТ:
#   1. bm25_search(query, top_k=50) → грубый отбор по ключевым словам
#   2. vector_search(query, top_k=50) → грубый отбор по семантике
#   3. rrf_fusion(bm25, vector)[:20] → объединение и сужение до 20
#   4. rerank(query, top20)[:5] → точное ранжирование → финальные 5
#
# Слайд 21: «Multi-stage Reranking — индустриальный стандарт 2025»
# =============================================================================

def only_vector_search(query: str, top_k: int = 5) -> list[dict]:
    """Только векторный поиск (baseline)."""
    results = vector_search(query, top_k=top_k)
    return [{"idx": idx, "doc": KNOWLEDGE_BASE[idx], "score": score}
            for idx, score in results]


def only_bm25_search(query: str, top_k: int = 5) -> list[dict]:
    """Только BM25 поиск (baseline)."""
    results = bm25_search(query, top_k=top_k)
    return [{"idx": idx, "doc": KNOWLEDGE_BASE[idx], "score": score}
            for idx, score in results]


def hybrid_rrf_search(query: str, top_k: int = 5) -> list[dict]:
    """Гибридный поиск BM25 + Vector + RRF (без реранкинга)."""
    bm25_results = bm25_search(query, top_k=50)
    vec_results = vector_search(query, top_k=50)
    rrf_results = rrf_fusion(bm25_results, vec_results)[:top_k]
    return [{"idx": idx, "doc": KNOWLEDGE_BASE[idx], "score": score}
            for idx, score in rrf_results]


def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Полный гибридный пайплайн с реранкингом.
    BM25 + Vector → RRF → Cross-encoder reranker.
    """
    # Шаг 1: широкий BM25
    bm25_results = bm25_search(query, top_k=50)
    # Шаг 2: широкий Vector
    vec_results = vector_search(query, top_k=50)
    # Шаг 3: RRF слияние → top-20 кандидатов
    candidates = rrf_fusion(bm25_results, vec_results)[:20]
    candidate_indices = [idx for idx, _ in candidates]
    # Шаг 4: точный реранкинг → top_k
    return rerank(query, candidate_indices, top_k=top_k)


# Сравнительная таблица методов
GOLDEN_DATASET = [
    {"question": "Какова чистая прибыль Сбербанка за Q1 2026?",      "relevant_idx": 0},
    {"question": "Почему Газпром не платит дивиденды?",               "relevant_idx": 1},
    {"question": "Каков прогноз роста выручки Яндекса в 2026 году?",  "relevant_idx": 2},
    {"question": "Какова выручка NVIDIA в четвёртом квартале FY2026?", "relevant_idx": 3},
    {"question": "Сколько автомобилей Tesla поставила в Q4 2025?",     "relevant_idx": 5},
    {"question": "Какие дивиденды платит ЛУКОЙЛ?",                    "relevant_idx": 6},
    {"question": "Каков прогноз добычи АЛРОСА на 2026 год?",           "relevant_idx": 8},
    {"question": "Какова дневная аудитория Meta в Q4 2025?",           "relevant_idx": 9},
]


def evaluate_method(search_fn, method_name: str, top_k: int = 5) -> dict:
    """Считает Hit Rate@K для метода поиска на GOLDEN_DATASET."""
    hits = 0
    for item in GOLDEN_DATASET:
        results = search_fn(item["question"], top_k=top_k)
        retrieved_indices = [r["idx"] for r in results]
        if item["relevant_idx"] in retrieved_indices:
            hits += 1
    hit_rate = hits / len(GOLDEN_DATASET)
    print(f"  {method_name:30s}: Hit Rate@{top_k} = {hit_rate:.2f} ({hits}/{len(GOLDEN_DATASET)})")
    return {"method": method_name, "hit_rate": hit_rate}


print("\n=== Сравнение методов поиска (Hit Rate@5) ===")
evaluate_method(only_vector_search, "Vector Only")
evaluate_method(only_bm25_search, "BM25 Only")
evaluate_method(hybrid_rrf_search, "Hybrid RRF (no rerank)")
evaluate_method(hybrid_search, "Hybrid RRF + Cross-encoder")


# =============================================================================
# SUMMARY 2: Шаги 4-5
# Полный пайплайн: BM25(50) + Vector(50) → RRF → top-20 → rerank → top-5.
# Cross-encoder улучшает MRR: правильный документ чаще на первой позиции.
# Для русского языка в production: Qwen3-Reranker-0.6B вместо ms-marco.
# Латентность: BM25 ~1ms, Vector ~5ms, CrossEncoder ~50ms на GPU.
# =============================================================================

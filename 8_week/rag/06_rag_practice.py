"""
ФАЙЛ 6: Разбор практики — Ноутбуки 1 и 2 + RAG по реальному PDF
================================================================
Документация: https://github.com/DS4SD/docling
Слайды: 6 (парсинг PDF), Ноутбук 1 (cell 4-52), Ноутбук 2 (cell 1-79)
"""

import os
import numpy as np
import anthropic
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# РАЗДЕЛ 1: РАЗБОР НОУТБУКА 1 (Базовые RAG-техники)
#
# ЧТО ЕСТЬ: ноутбук с базовым RAG пайплайном
# ЧТО ДЕЛАЕМ: разбираем каждую ключевую ячейку — зачем она и как работает
# КАК РАБОТАЕТ:
#   Этот раздел — текстовый walkthrough, дополненный рабочим кодом
#   Каждый CELL N соответствует ячейке в ноутбуке 1
#
# Слайд 6: «Ноутбуки = живая документация к слайдам»
# =============================================================================

print("=" * 60)
print("РАЗДЕЛ 1: Разбор Ноутбука 1 — Базовые RAG-техники")
print("=" * 60)

# ---------------------------------------------------------------------------
# CELL 7: База знаний вкладов → зачем структура словарей?
# ---------------------------------------------------------------------------
# ЧТО ДЕЛАЕТСЯ: создаётся список словарей с параметрами вкладов банков
# ПОЧЕМУ ТАК: словарь позволяет to_text() гибко собирать разные поля в строку
# АНАЛОГ В НАШЕМ ФАЙЛЕ: KNOWLEDGE_BASE в файлах 01-05 — та же структура
#
# Пример структуры из ноутбука 1:
CELL_7_EXAMPLE = {
    "bank": "Сбербанк",
    "product": "Вклад Классический",
    "rate": "16.5%",
    "term_days": 365,
    "min_amount": 100_000,
    "features": "пополнение, частичное снятие",
}

def to_text_example(doc: dict) -> str:
    """Функция из ноутбука 1: собирает поля словаря в строку."""
    # Объединение полей в строку — это ключевой шаг перед encode()
    return " | ".join(f"{k}: {v}" for k, v in doc.items())

print("\nCELL 7: Пример структуры документа:")
print(f"  {to_text_example(CELL_7_EXAMPLE)}")

# CELL 14-16: SentenceTransformer + encode() + cosine_similarity
# ТОНКОСТЬ: encode(corpus) → [N,D], encode([query]) → [1,D]
# encode(query) без [] → вектор по символам строки (частая ошибка!)
print("\nCELL 14-16: encode(corpus)→[N,D] | encode([query])→[1,D] | encode(query)→ ошибка!")


# ---------------------------------------------------------------------------
# CELL 22: Функция search() — ключевая функция всего пайплайна
# ---------------------------------------------------------------------------
# КАК РАБОТАЕТ:
#   1. query_vec = embed_model.encode([query]) → shape [1, D]
#   2. similarities = cosine_similarity(query_vec, doc_embeddings)[0] → shape [N]
#   3. np.argsort(similarities)[::-1][:top_k] → индексы top-K
# ВАЖНО: [::-1] разворачивает argsort (ascending → descending)

print("\nCELL 22: Разбор search():")
print("  np.argsort(scores)       → [idx_мин, ..., idx_макс]  (ascending)")
print("  np.argsort(scores)[::-1] → [idx_макс, ..., idx_мин]  (descending)")
print("  [::-1][:top_k]           → индексы top-K наиболее похожих")


def demo_search_logic():
    """Демонстрация логики argsort для понимания поиска."""
    scores = np.array([0.3, 0.8, 0.1, 0.95, 0.6])
    print(f"\n  Пример scores: {scores}")
    print(f"  argsort: {np.argsort(scores)} (от мин к макс)")
    print(f"  [::-1]:  {np.argsort(scores)[::-1]} (от макс к мин)")
    print(f"  top-3:   {np.argsort(scores)[::-1][:3]} (индексы лучших 3)")

demo_search_logic()


# ---------------------------------------------------------------------------
# CELL 29: calculate_metrics() — как считается Hit Rate и MRR
# ---------------------------------------------------------------------------
# HIT RATE: бинарная метрика (попал/не попал) → mean() = доля попаданий
# MRR: учитывает ПОЗИЦИЮ правильного документа (rank 1 лучше чем rank 5)
# КОГДА MRR > HIT RATE: когда правильный документ всегда на первом месте
#   MRR = 1.0 означает: каждый раз правильный документ на позиции 1

print("\nCELL 29: Разбор метрик:")
print("  Hit Rate: [1, 0, 1, 1, 0] → mean = 0.60 (3 из 5 нашли)")
print("  MRR: ранги [1, -, 3, 2, -] → [1.0, 0, 0.33, 0.5, 0] → mean = 0.37")
print("  Hit Rate = 0.60, MRR = 0.37: нашли но не всегда на первом месте")
print("  Если всегда на rank 1: Hit Rate = MRR = 1.0")


# ---------------------------------------------------------------------------
# CELL 35-37: CrossEncoder для реранкинга
# ---------------------------------------------------------------------------
# ЗАЧЕМ: bi-encoder быстрый но менее точный (раздельное кодирование)
#         cross-encoder медленный но точный (совместное кодирование пары)
# PIPELINE: top-50 (bi-encoder) → top-5 (cross-encoder) = скорость + точность
# Конкретно:
#   Bi-encoder: encode(query) отдельно, encode(doc) отдельно → cos_sim
#   Cross-encoder: encode(query + [SEP] + doc) вместе → scalar score

print("\nCELL 35-37: Bi-encoder vs Cross-encoder:")
print("  Bi-encoder:    encode(query) ⊕ encode(doc) → fast, ~1ms на GPU")
print("  Cross-encoder: encode(query + doc) → точнее, ~10ms на GPU")
print("  Pipeline: top-50 (bi) → top-5 (cross) = лучший баланс")


# ---------------------------------------------------------------------------
# CELL 38-41: LLM-as-judge для оценки качества ответов
# ---------------------------------------------------------------------------
# ЗАЧЕМ: автоматически оценивает качество ответа LLM без человека
# КАК: LLM-судья получает вопрос + ответ + контекст → оценка 1-10
# ПРОМПТ судьи из ноутбука 1:

LLM_JUDGE_PROMPT_EXAMPLE = """Оцени качество ответа финансового ассистента от 1 до 10.

Вопрос: {question}
Контекст (источники): {context}
Ответ ассистента: {answer}

Критерии оценки:
- 9-10: ответ точный, полностью основан на контексте, без домыслов
- 7-8:  ответ правильный, но неполный или есть незначительные неточности
- 5-6:  ответ частично верный, есть ошибки или выход за контекст
- 1-4:  ответ неверный или является галлюцинацией

Оценка (только цифра):"""

print("\nCELL 38-41: LLM-as-judge промпт (сокращённо):")
print("  Судья оценивает: точность + грounding (только на основе контекста?)")
print("  Автоматизирует то, что раньше делал человек вручную")
print(f"  Пример промпта (первые 100 симв): '{LLM_JUDGE_PROMPT_EXAMPLE[:100]}...'")


# =============================================================================
# РАЗДЕЛ 2: РАЗБОР НОУТБУКА 2 (Продвинутые RAG-техники)
#
# ЧТО ЕСТЬ: ноутбук с 10 продвинутыми техниками RAG
# ЧТО ДЕЛАЕМ: разбираем ключевые архитектурные решения каждой техники
# КАК РАБОТАЕТ:
#   Фокус на "почему" — объясняем мотивацию каждой техники
# =============================================================================

print("\n")
print("=" * 60)
print("РАЗДЕЛ 2: Разбор Ноутбука 2 — Продвинутые RAG-техники")
print("=" * 60)

# ---------------------------------------------------------------------------
# ЧАСТЬ 1 (Cells 1-9): Baseline setup
# ---------------------------------------------------------------------------
# ЗАЧЕМ chromadb: in-memory хранение векторов без отдельного сервера
#   chromadb.Client() → всё в RAM, не нужен Docker или отдельный процесс
#   Для production: Qdrant (Docker, персистентность, масштабирование)
#
# ЗАЧЕМ all-MiniLM-L6-v2: лёгкая английская модель для демонстрации концепций
#   22M параметров, 384 dim, быстрая — хороша для учёбы, не для русского
#   В production русских текстов: paraphrase-multilingual-MiniLM-L12-v2 (наш выбор)
#   Ещё лучше: Qwen/Qwen3-Embedding-0.6B (специально для русского/китайского)
#
# СТРУКТУРА compute_metrics() из ноутбука 2:
#   def compute_metrics(search_fn, dataset) → {"mrr": ..., "hit_rate": ..., "ndcg": ...}
#   Принимает search_fn как параметр → легко сравнивать разные методы!

print("\nCells 1-9 (Baseline):")
print("  chromadb.Client()          → in-memory база, нет Docker")
print("  all-MiniLM-L6-v2           → 22M params, только английский")
print("  compute_metrics(search_fn) → search_fn как аргумент = удобное сравнение")
print()
print("  Почему не Qdrant с самого начала?")
print("  → Qdrant требует Docker или pip install qdrant-client + сервер")
print("  → chromadb быстрее запускается для учебных примеров")


# ---------------------------------------------------------------------------
# ЧАСТЬ 3 (Cells 16-18): Query Expansion
# ---------------------------------------------------------------------------
# КАК expand_query() работает через ChatOpenAI в ноутбуке 2:
#   llm = ChatOpenAI(model="gpt-4o-mini")
#   prompt = f"Generate {n} alternative search queries for: {query}"
#   response = llm.invoke(prompt)
#   queries = response.content.strip().split("\n")[:n]
#
# КЛЮЧЕВАЯ ДЕТАЛЬ: результаты от всех вариантов объединяются + дедупликация
#   set(results_variant1 | results_variant2 | results_variant3)
# ТРЕЙДОФ: N вариантов → N раз поиск → N раз дольше

print("\nCells 16-18 (Query Expansion): recall↑ vs latency↑ (N*поиск)")


# ---------------------------------------------------------------------------
# ЧАСТЬ 5 (Cells 22-24): Parent Document Retrieval
# ---------------------------------------------------------------------------
# КЛЮЧЕВАЯ ДЕТАЛЬ: child_splitter(chunk_size=150) — маленькие чанки для ПОИСКА
#                  parent_splitter(chunk_size=600) — большие чанки для КОНТЕКСТА
#
# InMemoryStore из LangChain: простой словарь {doc_id: content}
#   store = InMemoryStore()
#   store.mset([(doc_id, parent_doc)])  # записываем родителя
#   store.mget([parent_id])             # читаем по ID
#
# ПОЧЕМУ ЭТО РАБОТАЕТ:
#   Маленький чанк "NIM=5.8%" → точное совпадение с запросом "NIM Сбербанка"
#   Возвращаем родителя (весь абзац) → LLM получает полный контекст

print("\nCells 22-24 (Parent Document Retrieval): child=150 поиск, parent=600 контекст")


# ---------------------------------------------------------------------------
# ЧАСТЬ 6 (Cells 25-28): Contextual Retrieval
# ---------------------------------------------------------------------------
# ОТКУДА: Anthropic blog post, сентябрь 2024
# СУТЬ: перед индексированием LLM добавляет контекст к каждому чанку
#
# ПРОМПТ из ноутбука 2 (упрощённо):
#   "Этот чанк взят из документа {title}.
#    Добавь 1-2 предложения, объясняющих ИЗ КАКОГО РАЗДЕЛА этот чанк
#    и О ЧЁМ идёт речь в этом разделе документа."
#
# СТОИМОСТЬ: N * LLM_call при ИНДЕКСИРОВАНИИ (офлайн, один раз)
#   При 100 чанках × claude-haiku ≈ $0.08 (индексирование один раз)
#   При каждом поиске: НОЛЬ дополнительных LLM вызовов (уже в векторах)

print("\nCells 25-28 (Contextual Retrieval): +15-20% Hit Rate, ~$0.08/100 чанков")


# ---------------------------------------------------------------------------
# ЧАСТЬ 7 (Cells 29-32): Late Chunking
# ---------------------------------------------------------------------------
# ОТЛИЧИЕ от обычного chunking:
#   Обычно: text → split → [chunk1, chunk2, ...] → encode(chunk_i) → vector_i
#            Каждый chunk_i кодируется НЕЗАВИСИМО = нет контекста других чанков
#
#   Late:   text → encode (весь) → [token_emb_1, ..., token_emb_N]
#                                         ↓ span pooling
#                                   [vec_chunk1, vec_chunk2, ...]
#           Каждый token "видит" все другие токены через self-attention!
#
# ЗАЧЕМ AutoModel напрямую (не SentenceTransformer):
#   SentenceTransformer.encode() → уже готовый sentence embedding
#   AutoModel.forward()  → token-level embeddings (нужны для span pooling)

print("\nCells 29-32 (Late Chunking): encode(весь_текст)→span pool → контекст для каждого чанка")


# ---------------------------------------------------------------------------
# ЧАСТЬ 10 (Cells 38-40): Agentic RAG
# ---------------------------------------------------------------------------
# ФУНКЦИЯ agentic_retrieve() из ноутбука 2:
#   def agentic_retrieve(query, max_retries=2):
#       results = search(query)
#       for _ in range(max_retries):
#           # LLM оценивает: достаточно ли контекста?
#           evaluation = llm.invoke(f"Достаточно ли контекста для ответа? {results}")
#           if "достаточно" in evaluation.lower():
#               break
#           # Уточняем запрос
#           refined = llm.invoke(f"Уточни запрос: {query}. Найденное: {results}")
#           results = search(refined)
#       return results
#
# max_retries=2 предотвращает бесконечный цикл (важно для production)
# Каждый retry = +1 LLM вызов + 1 поиск = задержка растёт

print("\nCells 38-40 (Agentic RAG): search→LLM judge→retry(max=2). Error rate -78% vs однократного")


# =============================================================================
# РАЗДЕЛ 3: RAG ПО РЕАЛЬНОМУ ФИНАНСОВОМУ PDF
#
# ЧТО ЕСТЬ: Tower Semiconductor Annual Report 2022 (Form 20-F, 158 стр.)
# ЧТО ДЕЛАЕМ: разбираем документ через Docling, строим RAG
# КАК РАБОТАЕТ:
#   1. Docling конвертирует PDF → Markdown с сохранением структуры
#   2. RecursiveCharacterTextSplitter нарезает на чанки
#   3. Чанки индексируются, система готова к вопросам
#
# Слайд 6: «Docling — лучший open-source парсер PDF для AI-пайплайнов (2025)»
# =============================================================================

print("\n")
print("=" * 60)
print("РАЗДЕЛ 3: RAG по реальному финансовому PDF")
print("=" * 60)

PDF_PATH = "/home/emkex/life/capital/areas/code/ai_engineer/8_week/rag/Пример.pdf"


def parse_pdf_to_markdown(pdf_path: str) -> str:
    """
    Конвертирует PDF в Markdown с сохранением структуры таблиц и заголовков.

    Docling (IBM Research) лучше чем pdfplumber/PyMuPDF для:
    - Таблиц (финансовые отчёты полны таблиц)
    - Колонок (годовые отчёты часто двухколоночные)
    - Формул и специальных символов

    Слайд 6: «Docling: layout-aware parsing для структурированных документов»
    """
    try:
        from docling.document_converter import DocumentConverter

        print(f"  Парсим PDF: {pdf_path}")
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        markdown_text = result.document.export_to_markdown()
        print(f"  Docling: конвертировано {len(markdown_text)} символов")
        return markdown_text

    except ImportError:
        print("  Docling не установлен. Установи: pip install docling")
        # Mock: возвращаем первые страницы Tower Semiconductor 20-F
        mock_text = """
# Tower Semiconductor Ltd. Annual Report 2022 (Form 20-F)

## Business Overview
Tower Semiconductor Ltd. is a leading foundry company for analog ICs.
Headquartered in Migdal Haemek, Israel. Founded 1993.
Customers: 300+ companies in automotive, industrial, medical, aerospace.

## Financial Highlights 2022
Revenue: $1,677 million (+25% year-over-year from $1,341M in 2021)
Operating income: $312 million (operating margin: 18.6%)
Net income: $269 million (+47% YoY)
EPS (diluted): $2.58 per share
EBITDA: $621 million (EBITDA margin: 37%)
R&D expenses: $112 million (6.7% of revenue)
Capital expenditures: $411 million (24.5% of revenue)

## Revenue by Segment
RF (Radio Frequency): $398M (24% of revenue)
Power Management: $285M (17% of revenue)
CMOS Image Sensors: $185M (11% of revenue)
Industrial/Other: $809M (48% of revenue)

## Key Business Risks
1. Customer concentration: top 5 customers = 45% of revenue
2. Fab utilization: fixed costs require >85% utilization for profitability
3. Geopolitical risks: operations in Israel and Japan
4. Competition from TSMC, GlobalFoundries, UMC
5. Raw material supply chain: silicon wafers, specialty gases
6. Technology obsolescence: 8-inch vs 12-inch transition

## Balance Sheet (December 31, 2022)
Total assets: $3,241 million
Total debt: $628 million
Cash and equivalents: $892 million
Net cash position: $264 million
Shareholders equity: $1,847 million

## Outlook 2023
Revenue guidance Q1 2023: $390-410 million
Management commentary: continued strong demand in power, automotive
Intel acquisition agreement: signed 2022, pending regulatory approval
"""
        return mock_text


# Golden dataset для Tower Semiconductor (финансовый домен — полупроводники)
TOWER_GOLDEN_DATASET = [
    {
        "question": "What was Tower Semiconductor revenue in 2022?",
        "ground_truth": "$1,677 million",
        "context_keyword": "revenue",
    },
    {
        "question": "What is Tower's operating margin in 2022?",
        "ground_truth": "18.6%",
        "context_keyword": "operating",
    },
    {
        "question": "What are the main business risks for Tower Semiconductor?",
        "ground_truth": "customer concentration, fab utilization, geopolitical risks",
        "context_keyword": "risk",
    },
    {
        "question": "What was Tower's net income in 2022?",
        "ground_truth": "$269 million",
        "context_keyword": "net income",
    },
    {
        "question": "What is Tower's EBITDA margin?",
        "ground_truth": "37%",
        "context_keyword": "ebitda",
    },
]


def simple_keyword_search(query: str, chunks: list[str], top_k: int = 3) -> list[str]:
    """
    Простой keyword поиск по чанкам PDF (без embedding-модели).
    Используется для демонстрации без загрузки тяжёлой модели.
    """
    query_words = set(query.lower().split())
    scored = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        # Jaccard-подобный скор: пересечение слов
        score = len(query_words & chunk_words)
        scored.append((score, chunk))
    scored.sort(reverse=True)
    return [chunk for _, chunk in scored[:top_k] if _ > 0]


def demo_pdf_rag():
    """Полный RAG пайплайн на реальном финансовом PDF."""
    print("\nЗапускаем RAG по финансовому PDF (Tower Semiconductor 20-F)")
    print("-" * 50)

    # Шаг 1: Парсинг PDF
    md_text = parse_pdf_to_markdown(PDF_PATH)
    print(f"Размер документа: {len(md_text)} символов")

    # Шаг 2: Чанкинг
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            # Приоритет разделителей: параграфы → строки → предложения
            separators=["\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_text(md_text)
        print(f"Чанков после разбивки: {len(chunks)}")
        print(f"Средний размер чанка: {sum(len(c) for c in chunks)//len(chunks)} символов")

    except ImportError:
        print("langchain не установлен — используем простое разбиение")
        # Простое разбиение по параграфам
        chunks = [p.strip() for p in md_text.split("\n\n") if len(p.strip()) > 50]
        print(f"Чанков (разбивка по параграфам): {len(chunks)}")

    # Шаг 3: Поиск + генерация через Claude Haiku
    print("\nRAG ответы через Claude Haiku:")
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    for item in TOWER_GOLDEN_DATASET[:3]:
        found_chunks = simple_keyword_search(item["question"], chunks, top_k=3)
        context = "\n\n".join(found_chunks) if found_chunks else "(чанки не найдены)"

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system="Ты финансовый аналитик. Отвечай ТОЛЬКО на основе предоставленного контекста. Кратко.",
            messages=[{"role": "user", "content":
                f"Контекст из Tower Semiconductor Annual Report 2022:\n{context}\n\n"
                f"Вопрос: {item['question']}"}],
        )
        print(f"\n  Q: {item['question']}")
        print(f"  Ground truth: {item['ground_truth']}")
        print(f"  Claude Haiku: {response.content[0].text.strip()}")


demo_pdf_rag()


# =============================================================================
# РАЗДЕЛ 4: PRODUCTION СТЕК
#
# ЧТО ЕСТЬ: учебные примеры из файлов 01-06
# ЧТО ДЕЛАЕМ: показываем как это выглядит в production
# КАК РАБОТАЕТ:
#   Каждый компонент выбран по конкретным критериям
#
# Слайд 57-58: «Production RAG — не один инструмент, а пайплайн»
# =============================================================================

print("\n")
print("=" * 60)
print("РАЗДЕЛ 4: Production стек (Слайды 57-58)")
print("=" * 60)

production_stack = {
    "embedding":     "Qwen/Qwen3-Embedding-0.6B (русский) или jina-embeddings-v3",
    "vector_db":     "Qdrant (production) или Chroma (dev/local)",
    "hybrid_search": "BM25 (rank_bm25) + Vector + RRF (k=60)",
    "reranking":     "Qwen/Qwen3-Reranker-0.6B или cross-encoder/ms-marco-MiniLM",
    "llm":           "Qwen2.5-3B-Instruct (local) или Claude Haiku (API)",
    "eval_offline":  "RAGAS (Faithfulness, Context Precision, Answer Relevancy)",
    "observability": "LangFuse (запросы, латентность, feedback)",
    "monitoring":    "Grafana + Prometheus (Hit Rate, P95 latency)",
}

print("\nРекомендуемый production стек:")
max_key_len = max(len(k) for k in production_stack)
for component, tool in production_stack.items():
    print(f"  {component:<15} → {tool}")

print("\nУчёба → Production:")
print("  paraphrase-multilingual → Qwen3-Embedding-0.6B")
print("  numpy cosine_similarity → Qdrant HNSW index")
print("  mock_llm()              → Claude Haiku / Qwen2.5-3B-Instruct")
print("  ручные метрики          → RAGAS + DeepEval CI/CD")
print("  print() логи            → LangFuse + Grafana")
print("\nКаждый компонент заменяем независимо — архитектура не меняется.")


# =============================================================================
# ЗАДАЧА (финансовый домен)
# =============================================================================
"""
ЗАДАЧА: Реализуй RAG по Пример.pdf

Контекст: Пример.pdf — это годовой отчёт Tower Semiconductor (Form 20-F, 2022).
Компания производит аналоговые микросхемы. Выручка $1.677B (+25% г/г).

Задание (5 шагов):

Шаг 1. Установи Docling и распарси PDF:
    pip install docling
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert("/путь/к/Пример.pdf")
    md_text = result.document.export_to_markdown()
    print(f"Размер: {len(md_text)} символов")

Шаг 2. Построй чанки и векторную базу:
    - chunk_size=500, chunk_overlap=100
    - Модель: paraphrase-multilingual-MiniLM-L12-v2
    - Проиндексируй все чанки

Шаг 3. Создай TOWER_GOLDEN_DATASET из 8 вопросов:
    - 3 вопроса о финансовых показателях (revenue, margins, EPS)
    - 3 вопроса о бизнес-рисках и стратегии
    - 2 вопроса о конкурентной позиции
    Для каждого: question + ground_truth + relevant_chunk_hint

Шаг 4. Запусти оценку через функции из файла 04_rag_metrics.py:
    hit_rate = hit_rate_at_k(TOWER_GOLDEN_DATASET, search, k=5)
    mrr_score = mrr(TOWER_GOLDEN_DATASET, search, k=5)
    print(f"Hit Rate@5: {hit_rate:.2f}, MRR: {mrr_score:.3f}")

Шаг 5. Если Hit Rate < 0.80:
    - Попробуй уменьшить chunk_size до 300
    - Попробуй contextual retrieval (функция из файла 03)
    - Добавь BM25 hybrid search (файл 02)
    Зафиксируй метрики каждого шага в таблицу.

Ожидаемый результат:
    Таблица: метод | Hit Rate@5 | MRR | Комментарий
    Simple vector  |    0.XX    | 0.XX | baseline
    Hybrid BM25+V  |    0.XX    | 0.XX | +BM25
    Contextual     |    0.XX    | 0.XX | +context
"""

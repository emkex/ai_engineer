"""
ФАЙЛ 3: Стратегии чанкинга — Fixed-size, Parent Doc Retrieval, Contextual, Late Chunking
======================================
Документация: https://python.langchain.com/docs/
Слайды: 7, 19–20, 23
"""

import os
import numpy as np
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Годовой отчёт FinTech Holdings — длинный финансовый документ для демонстрации чанкинга
ANNUAL_REPORT = """
ГОДОВОЙ ОТЧЁТ: FinTech Holdings 2025
=====================================

РАЗДЕЛ 1. ФИНАНСОВЫЕ РЕЗУЛЬТАТЫ
Выручка группы за 2025 год составила 487 млрд рублей, что на 42% выше показателя 2024 года (343 млрд руб).
Операционная прибыль выросла до 89 млрд рублей (+38%). Рентабельность по EBITDA составила 21.3%.
Чистая прибыль: 52 млрд рублей (+55% г/г). EPS: 26.0 руб/акция. Дивиденды за 2025: 12 руб/акция.

РАЗДЕЛ 2. СЕГМЕНТЫ БИЗНЕСА
Платёжный сегмент: GMV 8.4 трлн руб (+65%). Take rate: 0.9%. Выручка сегмента: 76 млрд руб.
Кредитный сегмент: портфель 380 млрд руб (+48%). NPL 3.2% (улучшение с 4.1%). NIM: 12.4%.
Инвестиционный сегмент: AUM 1.1 трлн руб (+80%). Комиссионная выручка: 22 млрд руб.
Страховой сегмент: GWP 45 млрд руб (+30%). Комбинированный коэффициент: 87%.

РАЗДЕЛ 3. РИСКИ
Рыночный риск: подверженность волатильности ставок ЦБ. Текущая ключевая ставка 16% влияет на стоимость фондирования.
Кредитный риск: концентрация в МСП (35% портфеля). Резерв под кредитные потери: 18 млрд руб (4.7% портфеля).
Операционный риск: инфраструктура обрабатывает 12 млн транзакций в сутки. Uptime 99.98%.
Регуляторный риск: лицензия Банка России на небанковскую кредитную организацию.

РАЗДЕЛ 4. СТРАТЕГИЯ 2026-2028
Цель: стать лидером финтех-рынка РФ с GMV 20 трлн руб к 2028 году.
Инвестиции в AI: 25 млрд руб в 2026 году (скоринг, фрод-детекция, персонализация).
Международная экспансия: выход на рынки СНГ в 2026, Юго-Восточная Азия в 2027.
M&A: переговоры с 3 региональными банками о приобретении.

РАЗДЕЛ 5. ESG
Углеродный след снижен на 18% в 2025 году. Data centres перешли на 60% возобновляемой энергии.
Гендерный баланс в совете директоров: 40% женщин. Текучесть кадров: 8% (ниже среднего по отрасли 15%).
"""


# =============================================================================
# ШАГ 1: FIXED-SIZE CHUNKING
#
# ЧТО ЕСТЬ: длинный финансовый документ (годовой отчёт)
# ЧТО ДЕЛАЕМ: нарезаем на фиксированные кусочки с перекрытием
# КАК РАБОТАЕТ:
#   1. RecursiveCharacterTextSplitter пытается разбить по параграфам (\n\n)
#   2. Если параграф длиннее chunk_size — разбивает по строкам (\n)
#   3. chunk_overlap: N символов с предыдущего чанка добавляется в начало
#
# Слайд 7: «Chunk size — компромисс: маленький = точный поиск, большой = полный контекст»
# =============================================================================

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Мелкие чанки: точный поиск, меньше контекста
    splitter_small = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=40,
        separators=["\n\n", "\n", ". ", " "],  # приоритет разделителей
    )

    # Крупные чанки: меньше точность поиска, больше контекста для LLM
    splitter_large = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "],
    )

    chunks_small = splitter_small.split_text(ANNUAL_REPORT)
    chunks_large = splitter_large.split_text(ANNUAL_REPORT)

    print("=== Fixed-Size Chunking ===")
    print(f"chunk_size=200: {len(chunks_small)} чанков, средний размер: {sum(len(c) for c in chunks_small)//len(chunks_small)} симв.")
    print(f"chunk_size=500: {len(chunks_large)} чанков, средний размер: {sum(len(c) for c in chunks_large)//len(chunks_large)} симв.")
    print(f"\nПример чанка (small #2):\n  '{chunks_small[1][:120]}...'")

    _langchain_available = True

except ImportError:
    print("Установи langchain: pip install langchain langchain-text-splitters")
    _langchain_available = False

    # Заглушка: простое разбиение по символам
    def _simple_split(text: str, size: int, overlap: int) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end].strip())
            start += size - overlap
        return [c for c in chunks if len(c) > 10]

    chunks_small = _simple_split(ANNUAL_REPORT, 200, 40)
    chunks_large = _simple_split(ANNUAL_REPORT, 500, 100)
    print(f"[Заглушка] chunk_size=200: {len(chunks_small)} чанков")
    print(f"[Заглушка] chunk_size=500: {len(chunks_large)} чанков")


# =============================================================================
# ШАГ 2: PARENT DOCUMENT RETRIEVAL
#
# ЧТО ЕСТЬ: документ с разными уровнями детализации
# ЧТО ДЕЛАЕМ: индексируем мелкие чанки, возвращаем крупные родительские
# КАК РАБОТАЕТ:
#   1. Делим документ на крупные "родительские" секции (chunk_size=600)
#   2. Каждую секцию делим на мелкие "дочерние" чанки (chunk_size=150)
#   3. При поиске: находим мелкий чанк → lookup → возвращаем весь родительский блок
#   Преимущество: поиск точный (по мелким), контекст полный (по крупным)
#
# Слайд 23: «Parent Document Retrieval — лучший из двух миров»
# =============================================================================

def build_parent_index(
    document: str,
    child_size: int = 150,
    parent_size: int = 600,
    child_overlap: int = 20,
    parent_overlap: int = 50,
) -> tuple[list[str], dict, dict]:
    """
    Строит двухуровневый индекс для Parent Document Retrieval.

    Возвращает:
        child_chunks: список мелких чанков для индексирования
        parent_store: {parent_id: текст родителя}
        child_to_parent: {child_idx: parent_id}
    """
    if _langchain_available:
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_size, chunk_overlap=child_overlap
        )
        parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_size, chunk_overlap=parent_overlap
        )
        parent_chunks = parent_splitter.split_text(document)
        child_chunks_all = []
        child_to_parent = {}
        parent_store = {}

        for p_idx, parent_text in enumerate(parent_chunks):
            parent_id = f"parent_{p_idx}"
            parent_store[parent_id] = parent_text
            # Делим родительский блок на дочерние чанки
            children = child_splitter.split_text(parent_text)
            for child in children:
                child_idx = len(child_chunks_all)
                child_chunks_all.append(child)
                child_to_parent[child_idx] = parent_id

    else:
        # Заглушка без LangChain
        parent_chunks = _simple_split(document, parent_size, parent_overlap)
        child_chunks_all = []
        child_to_parent = {}
        parent_store = {}

        for p_idx, parent_text in enumerate(parent_chunks):
            parent_id = f"parent_{p_idx}"
            parent_store[parent_id] = parent_text
            children = _simple_split(parent_text, child_size, child_overlap)
            for child in children:
                child_idx = len(child_chunks_all)
                child_chunks_all.append(child)
                child_to_parent[child_idx] = parent_id

    return child_chunks_all, parent_store, child_to_parent


child_chunks, parent_store, child_to_parent = build_parent_index(ANNUAL_REPORT)

print("\n=== Parent Document Retrieval ===")
print(f"Родительских блоков: {len(parent_store)}")
print(f"Дочерних чанков (для поиска): {len(child_chunks)}")
print(f"Пример дочернего чанка #0:\n  '{child_chunks[0][:100]}...'")
print(f"Его родитель (parent_0, первые 150 симв.):\n  '{parent_store['parent_0'][:150]}...'")


# Embedding-поиск по дочерним чанкам → возврат родительского блока
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

print("\nВекторизация дочерних чанков...")
child_embeddings = embed_model.encode(child_chunks, show_progress_bar=False)


def parent_search(query: str, top_k: int = 3) -> list[str]:
    """
    Поиск по дочерним чанкам → возврат родительских блоков.
    Дедуплицирует: один родитель не возвращается дважды.
    """
    query_vec = embed_model.encode([query])
    scores = cosine_similarity(query_vec, child_embeddings)[0]
    sorted_indices = np.argsort(scores)[::-1]

    seen_parents = set()
    result_parents = []
    for child_idx in sorted_indices:
        parent_id = child_to_parent[int(child_idx)]
        if parent_id not in seen_parents:
            seen_parents.add(parent_id)
            result_parents.append(parent_store[parent_id])
        if len(result_parents) >= top_k:
            break

    return result_parents


print("\nParent search: 'дивиденды и прибыль FinTech Holdings'")
parent_results = parent_search("дивиденды и прибыль FinTech Holdings", top_k=2)
for i, text in enumerate(parent_results, 1):
    print(f"  Родитель {i} ({len(text)} симв.): '{text[:100]}...'")


# =============================================================================
# SUMMARY 1: Шаги 1-2
# Fixed-size: просто, быстро, работает всегда — стартовая точка.
# Parent Doc Retrieval: точный поиск (child) + полный контекст (parent).
# chunk_overlap важен: без него граничные предложения теряются.
# Для финансовых отчётов с разделами parent_size=600 покрывает целый раздел.
# =============================================================================


# =============================================================================
# ШАГ 3: CONTEXTUAL RETRIEVAL
#
# ЧТО ЕСТЬ: мелкие чанки без контекста документа
# ЧТО ДЕЛАЕМ: LLM добавляет контекст к каждому чанку перед embedding
# КАК РАБОТАЕТ:
#   Проблема: чанк "NIM: 12.4%" непонятен без контекста ("чей NIM?")
#   Решение: LLM добавляет 1-2 предложения с контекстом документа
#   Результат: "Годовой отчёт FinTech Holdings 2025, кредитный сегмент. NIM: 12.4%."
#   Hit Rate улучшается на +15-20% (Anthropic, 2024)
#
# Слайд 19: «Contextual Retrieval — добавляем контекст до индексирования, не после»
# =============================================================================

def contextualize_chunk(full_doc: str, chunk: str, title: str) -> str:
    """
    Claude Haiku добавляет контекст к каждому чанку перед embedding.

    Слайд 19: Contextual Retrieval (Anthropic, 2024) — +15-20% Hit Rate.
    Стоимость: N вызовов Claude при индексировании (офлайн, один раз).
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=80,
        system="Ты помощник по индексированию финансовых документов. Отвечай кратко — 1-2 предложения.",
        messages=[{"role": "user", "content":
            f"Документ: {title}\n\n"
            f"Чанк из документа:\n{chunk}\n\n"
            f"Добавь 1-2 предложения с контекстом: из какого раздела этот чанк "
            f"и о каком финансовом показателе/компании идёт речь. "
            f"Только контекст, без повторения самого чанка."}],
    )
    context_prefix = response.content[0].text.strip()
    return f"{context_prefix} {chunk}"


# Применяем контекстуализацию ко всем чанкам
contextual_chunks = [
    contextualize_chunk(ANNUAL_REPORT, c, "Годовой отчёт FinTech Holdings 2025")
    for c in chunks_small
]

print("\n=== Contextual Retrieval ===")
print(f"Всего чанков: {len(contextual_chunks)}")
print(f"\nДо контекстуализации:\n  '{chunks_small[3][:100]}'")
print(f"\nПосле контекстуализации:\n  '{contextual_chunks[3][:130]}'")

# Стоимость: N вызовов LLM при индексировании (офлайн, один раз)
print(f"\nСтоимость индексирования: ~{len(chunks_small)} LLM вызовов (офлайн, один раз)")
print("Для claude-haiku-4-5: ~$0.0008 за чанк × 200 чанков = ~$0.16 за документ")


# =============================================================================
# ШАГ 4: LATE CHUNKING
#
# ЧТО ЕСТЬ: документ, который нужно разбить на чанки с сохранением контекста
# ЧТО ДЕЛАЕМ: кодируем весь документ сразу, потом делаем pooling по span-ам
# КАК РАБОТАЕТ:
#   Обычный chunking: chunk → encode → вектор (каждый чанк независим)
#   Late chunking:
#     1. Весь текст → tokenizer → token IDs
#     2. Модель → token embeddings [seq_len, hidden_dim]
#     3. Определяем span (start, end) для каждого чанка
#     4. Mean pooling по span → вектор чанка с глобальным контекстом
#   Преимущество: каждый чанк "видит" весь документ через self-attention
#
# Слайд 20: «Late Chunking (Jina AI, 2024): глобальный контекст для каждого чанка»
# =============================================================================

try:
    import torch
    from transformers import AutoTokenizer, AutoModel

    # Для production использовать: jina-embeddings-v3 (поддерживает 8192 токенов)
    # Здесь: та же multilingual модель для демонстрации концепции
    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()

    def late_chunking_embed(text: str, chunk_texts: list[str]) -> list[np.ndarray]:
        """
        Late Chunking: кодируем весь документ, потом span-pooling по чанкам.

        Параметры:
            text: полный текст документа
            chunk_texts: список строк-чанков (те же данные, что разбил splitter)

        Возвращает список векторов — по одному на каждый чанк.
        """
        # Ограничиваем длину для демонстрации (модель поддерживает 512 токенов)
        text_short = text[:2000]

        # Шаг 1: токенизируем весь документ
        full_tokens = tokenizer(
            text_short,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            return_offsets_mapping=True,  # нужно для маппинга символов → токены
        )
        offset_mapping = full_tokens.pop("offset_mapping")[0]  # убираем из inputs

        # Шаг 2: прогоняем через модель → token embeddings
        with torch.no_grad():
            outputs = model(**full_tokens)
        token_embeddings = outputs.last_hidden_state[0]  # [seq_len, hidden_dim]

        # Шаг 3 и 4: для каждого чанка найти span в токенах и сделать mean pooling
        chunk_vectors = []
        char_offset = 0

        for chunk_text in chunk_texts:
            chunk_start_char = text_short.find(chunk_text[:50], char_offset)
            if chunk_start_char == -1:
                chunk_start_char = char_offset

            chunk_end_char = chunk_start_char + len(chunk_text)
            char_offset = chunk_start_char + 1

            # Находим токены, покрывающие этот span символов
            token_mask = []
            for token_start, token_end in offset_mapping.tolist():
                # Токен попадает в span если пересекается с ним
                overlaps = token_start < chunk_end_char and token_end > chunk_start_char
                token_mask.append(overlaps and token_start < token_end)

            token_mask_t = torch.tensor(token_mask, dtype=torch.bool)

            if token_mask_t.sum() > 0:
                # Mean pooling по токенам чанка
                span_vectors = token_embeddings[token_mask_t]
                chunk_vec = span_vectors.mean(dim=0).numpy()
            else:
                # Fallback: используем [CLS] токен
                chunk_vec = token_embeddings[0].numpy()

            chunk_vectors.append(chunk_vec)

        return chunk_vectors

    # Демонстрация: late chunking на первых 5 чанках
    demo_chunks = chunks_small[:5]
    print("\n=== Late Chunking ===")
    print(f"Кодируем документ целиком + span pooling для {len(demo_chunks)} чанков...")

    late_vectors = late_chunking_embed(ANNUAL_REPORT, demo_chunks)
    print(f"Размер вектора чанка: {late_vectors[0].shape}")
    print(f"Пример: чанк 0 и чанк 1 cosine similarity (поздний контекст):")
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim
    sim = cos_sim([late_vectors[0]], [late_vectors[1]])[0][0]
    print(f"  Late chunking: {sim:.3f}")

    # Для сравнения — обычный encoding
    std_vecs = embed_model.encode(demo_chunks)
    sim_std = cos_sim([std_vecs[0]], [std_vecs[1]])[0][0]
    print(f"  Standard encode: {sim_std:.3f}")

    _late_chunking_available = True

except ImportError:
    print("\nLate Chunking требует: pip install torch transformers")
    _late_chunking_available = False
    late_vectors = [np.zeros(384) for _ in chunks_small[:5]]


# =============================================================================
# SUMMARY 2: Шаги 3-4
# Contextual Retrieval: LLM добавляет контекст офлайн перед индексированием.
# Late Chunking: один forward pass → все чанки сохраняют глобальный контекст.
# Contextual Retrieval: +15-20% Hit Rate, требует N*LLM_call при индексировании.
# Late Chunking: работает без LLM при индексировании, нужна длинная модель.
# =============================================================================


# =============================================================================
# ШАГ 5: СРАВНЕНИЕ СТРАТЕГИЙ
#
# ЧТО ЕСТЬ: четыре реализованных метода чанкинга
# ЧТО ДЕЛАЕМ: выводим сравнительную таблицу характеристик
# КАК РАБОТАЕТ:
#   Показываем ключевые trade-offs для выбора метода в production
#
# Слайд 24: «Выбор стратегии чанкинга — первое архитектурное решение RAG»
# =============================================================================

print("\n=== Сравнение стратегий чанкинга ===")
print(f"{'Метод':<25} {'Чанков':>7} {'Ср.размер':>10} {'Контекст':>12} {'Стоимость':>12}")
print("-" * 70)

strategies = [
    ("fixed-size-small",  len(chunks_small),    sum(len(c) for c in chunks_small)//max(len(chunks_small),1),    "Нет",    "Низкая"),
    ("fixed-size-large",  len(chunks_large),    sum(len(c) for c in chunks_large)//max(len(chunks_large),1),    "Нет",    "Низкая"),
    ("parent-doc",        len(child_chunks),    sum(len(c) for c in child_chunks)//max(len(child_chunks),1),    "Частично","Низкая"),
    ("contextual",        len(contextual_chunks),sum(len(c) for c in contextual_chunks)//max(len(contextual_chunks),1),"Да","Высокая (LLM)"),
    ("late-chunking",     len(chunks_small),    sum(len(c) for c in chunks_small)//max(len(chunks_small),1),    "Да",     "Средняя"),
]

for method, n_chunks, avg_size, context, cost in strategies:
    print(f"{method:<25} {n_chunks:>7} {avg_size:>10} {context:>12} {cost:>12}")

print("\nРекомендации для финансовых документов (годовые отчёты, 10-K/20-F):")
print("  Старт:       fixed-size-large (chunk_size=500, overlap=100)")
print("  Улучшение:   parent-doc (child=150, parent=600) — разделы документа")
print("  Production:  contextual + hybrid search + cross-encoder reranking")


# =============================================================================
# ЗАДАЧА (финансовый домен)
# =============================================================================
"""
ЗАДАЧА: Эксперимент с чанкингом на реальном финансовом тексте

Контекст: Тебе нужно построить RAG для ответов на вопросы по годовым отчётам
российских эмитентов (SBER, GAZP, LKOH). Каждый отчёт — 50-200 страниц.

Задание:
1. Расширь ANNUAL_REPORT: добавь ещё 2 раздела (РАЗДЕЛ 6 и 7):
   - "РАЗДЕЛ 6. КОРПОРАТИВНОЕ УПРАВЛЕНИЕ"
     (Совет директоров, аудитор, дивидендная политика)
   - "РАЗДЕЛ 7. ПРОГНОЗ НА 2026 ГОД"
     (таргеты по выручке, прибыли, ключевые инициативы)

2. Создай GOLDEN_DATASET из 6 вопросов с указанием нужного раздела:
   {"question": "Каков размер дивидендов за 2025 год?", "relevant_section": "РАЗДЕЛ 1"}

3. Проведи сравнение двух стратегий:
   - fixed-size-small (chunk_size=200)
   - parent-doc (child=150, parent=600)
   Метрика: Hit Rate@5 (нашёл ли нужный раздел в топ-5)

4. Ответь на вопросы:
   - Какой chunk_size оптимален для финансовых отчётов?
   - Почему parent-doc лучше для вопросов типа "расскажи про риски"?
   - Что произойдёт с Hit Rate если сделать chunk_size=50?

Бонус: реализуй "семантическое" разбиение по разделам документа:
  - Найди все строки вида "РАЗДЕЛ N." через regex
  - Используй их как natural boundaries вместо фиксированного chunk_size
"""

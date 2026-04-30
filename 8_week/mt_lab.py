import os
from pathlib import Path

# -------------------------
# Загрузка документов

from langchain_community.document_loaders import RecursiveUrlLoader

os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

ROOT_URL = "https://mt-lab.su/"
PERSIST_DIR = Path(__file__).parent / "chroma_db_mt_lab"

recursive_loader = RecursiveUrlLoader(
    url=ROOT_URL,
    max_depth=3,
    prevent_outside=True,
)
docs = recursive_loader.load()
print(f"Total documents: {len(docs)}")
print(f"Total characters: {sum(len(d.page_content) for d in docs)}")

# -------------------------
# Сплиттер

from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

text_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.HTML,
    chunk_size=1200,
    chunk_overlap=200,
)
splits = text_splitter.split_documents(docs)

# -------------------------
# Embeddings

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

base_embeddings = HuggingFaceEmbeddings(model_name="ai-forever/ru-en-RoSBERTa")

class PrefixedEmbeddings(Embeddings):
    def __init__(self, base, query_prefix="", doc_prefix=""):
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    def embed_documents(self, texts):
        return self.base.embed_documents([self.doc_prefix + t for t in texts])

    def embed_query(self, text):
        return self.base.embed_query(self.query_prefix + text)

embeddings = PrefixedEmbeddings(
    base_embeddings,
    query_prefix="search_query: ",
    doc_prefix="search_document: ",
)

# -------------------------
# Vector store (загружаем существующий или создаём новый)

from langchain_community.vectorstores import Chroma

if PERSIST_DIR.exists():
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=str(PERSIST_DIR),
    )
    # Добавляем только те чанки, чей source ещё не в базе
    existing_sources = set(
        m["source"]
        for m in vectorstore.get(include=["metadatas"])["metadatas"]
        if m and "source" in m
    )
    new_splits = [s for s in splits if s.metadata.get("source") not in existing_sources]
    if new_splits:
        print(f"Добавляем {len(new_splits)} новых чанков из {len(set(s.metadata.get('source') for s in new_splits))} URL")
        vectorstore.add_documents(new_splits)
    else:
        print("Новых документов нет, база актуальна")
else:
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR),
    )

# -------------------------
# Retriever с MMR

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 8, "fetch_k": 32, "lambda_mult": 0.8},
)

# -------------------------
# Post-processing

MAX_CHARS = 10_000

def format_docs(docs):
    formatted = []
    total_len = 0
    for doc in docs:
        source = doc.metadata.get("source", "unknown_source")
        page = doc.metadata.get("page", None)
        header = f"Source: {source}" + (f" | Page: {page}" if page is not None else "")
        block = f"{header}\n{doc.page_content.strip()}"
        if total_len + len(block) > MAX_CHARS:
            break
        formatted.append(block)
        total_len += len(block)
    return "\n\n---\n\n".join(formatted)

# -------------------------
# Промпт

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a precise analytical assistant specializing in laboratory equipment of MT-LAB. "
        "Always respond in the same language the user used in their question. "
        "Rules:\n"
        "- Answer ONLY based on the provided context\n"
        "- If the answer is not in the context, say so directly — do not guess\n"
        "- Do not use external knowledge or make assumptions\n"
        "- Be concise but complete — include formulas, steps, or examples if present in context\n"
        "- If context contains contradictions, point them out\n"
        "- Always end your answer with: Sources: [filename, page X] for each chunk used"
    ),
    MessagesPlaceholder("history"),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

# -------------------------
# LLM

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Выбор провайдера: "ollama" или "anthropic"
LLM_PROVIDER = "anthropic"

def llm_part(provider: str = LLM_PROVIDER):
    if provider == "anthropic":
        from dotenv import load_dotenv
        load_dotenv()
        return ChatAnthropic(
            model="claude-haiku-4-5",
            temperature=0.2,
            max_tokens=1024,
        )
    try:
        llm = ChatOpenAI(
            api_key="None",
            base_url="http://127.0.0.1:11434/v1",
            model="gemma3:4b",
            temperature=0.2,
            max_tokens=1024,
            top_p=0.8,
        )
        return llm
    except Exception as e:
        print(f"Ollama недоступна, переключаемся на Anthropic: {e}")
        return llm_part("anthropic")

# -------------------------
# RAG-цепочка

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

def ensure_context(input_dict: dict) -> dict:
    if not input_dict.get("context", "").strip():
        input_dict["context"] = (
            "Контекст пуст: ретривер не нашёл ни одного подходящего фрагмента. "
            "Сообщи пользователю об этом и предложи связаться напрямую по телефону или другим способом."
        )
    return input_dict

rag_lab_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
        "history": lambda _: [],
    }
    | RunnableLambda(ensure_context)
    | prompt
    | llm_part()
    | StrOutputParser()
).with_config(run_name="rag_lab_chain")

# -------------------------

print(rag_lab_chain.invoke("Что такое MT-LAB?"))
print(rag_lab_chain.invoke("Какую мебель продают в MT-LAB?"))
print(rag_lab_chain.invoke("Способы связи?"))

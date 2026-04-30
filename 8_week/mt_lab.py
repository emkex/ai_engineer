# Загрузка документов (1)
import os
from langchain_community.document_loaders import SitemapLoader, RecursiveUrlLoader

os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

ROOT_URL = "https://mt-lab.su/"
SITEMAP_URL = f"{ROOT_URL}/sitemap-part-categories-chunk-0.xml" # один из sitemap, который точно существует

# # 1) Загружаем все страницы из sitemap
# sitemap_loader = SitemapLoader(
#     web_path=SITEMAP_URL,
#     filter_urls=[ROOT_URL],  # на всякий случай ограничиваем доменом
# )

# sitemap_docs = sitemap_loader.load()

# only one page in sitemap
# Total documents: 18
# Total characters: 26043

# 2) Дополнительно рекурсивно обходим сайт от корня
recursive_loader = RecursiveUrlLoader(
    url=ROOT_URL,
    max_depth=1,          # глубину при желании можно увеличить
    prevent_outside=True  # не выходим за пределы домена
)
docs = recursive_loader.load()

# depth=2
# Total documents: 29
# Total characters: 2808801

# depth=3
# Total documents: 34
# Total characters: 3160292


# # 3) Объединяем всё в один список документов для RAG
# # docs = sitemap_docs + recursive_docs
# docs = recursive_docs

print(f"Total documents: {len(docs)}")
print(f"Total characters: {sum(len(doc.page_content) for doc in docs)}")

# ----------------------
# Подготовка эмбеддингов

from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

text_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.HTML,   # учитываем структуру HTML
    chunk_size=1200,          # немного больше, т.к. структура сохраняется лучше
    chunk_overlap=200,
)

splits = text_splitter.split_documents(docs)

# -----------------------
# Подготовка текстов с префиксами, чтобы из них сделать эмбеддинги, которые передадим в модель для лучшего понимания, откуда текст – для запрос или из документа

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

# Базовая модель
base_embeddings = HuggingFaceEmbeddings(
    model_name="ai-forever/ru-en-RoSBERTa"
)

class PrefixedEmbeddings(Embeddings):
    def __init__(self, base, query_prefix="", doc_prefix=""):
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    def embed_documents(self, texts):
        texts_prefixed = [self.doc_prefix + t for t in texts]
        return self.base.embed_documents(texts_prefixed)

    def embed_query(self, text):
        return self.base.embed_query(self.query_prefix + text)

embeddings = PrefixedEmbeddings(
    base_embeddings,
    query_prefix="search_query: ",
    doc_prefix="search_document: ",
)

# -------------------------
# Создание и сохранение векторной базы данных для того, чтобы иметь место для хранения эмбеддингов и возможности быстро их загружать при последующих запусках, не тратя время на пересоздание

from pathlib import Path
from langchain_community.vectorstores import Chroma

persist_directory = "./chroma_db_mt_lab"

if Path(persist_directory).exists():
    # Индекс уже есть – просто загружаем
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )
else:
    # Первый запуск – создаём индекс
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_directory,
    )

print('finish')
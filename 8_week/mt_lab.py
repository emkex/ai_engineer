# Загрузка документов
import os
from langchain_community.document_loaders import SitemapLoader, RecursiveUrlLoader

os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

ROOT_URL = "https://mt-lab.su/"
SITEMAP_URL = f"{ROOT_URL}/sitemap-part-categories-chunk-0.xml" # один из sitemap, который точно существует

# 1) Загружаем все страницы из sitemap
sitemap_loader = SitemapLoader(
    web_path=SITEMAP_URL,
    filter_urls=[ROOT_URL],  # на всякий случай ограничиваем доменом
)

sitemap_docs = sitemap_loader.load()

# # 2) Дополнительно рекурсивно обходим сайт от корня
# recursive_loader = RecursiveUrlLoader(
#     url=ROOT_URL,
#     max_depth=2,          # глубину при желании можно увеличить
#     prevent_outside=True  # не выходим за пределы домена
# )
# recursive_docs = recursive_loader.load()

# # 3) Объединяем всё в один список документов для RAG
# # docs = sitemap_docs + recursive_docs
# docs = recursive_docs

print(f"Total documents: {len(sitemap_docs)}")
print(f"Total characters: {sum(len(doc.page_content) for doc in sitemap_docs)}")


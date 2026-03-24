import os
import json
import time
import requests
from bs4 import BeautifulSoup as BS
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════
# ТЕМА: requests + Session + куки из .env
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   Куки и токены — в .env, не в коде. Всегда.
#   Загружаются через python-dotenv:
#     load_dotenv()             # ищет .env рядом со скриптом
#     os.environ.get('KEY')     # читает переменную
#
#   requests.Session() — объект переиспользующий:
#     - TCP-соединение (быстрее)
#     - заголовки (установил один раз → действуют на все запросы)
#     - куки (автоматически сохраняются между запросами)
#
#   session.cookies.update({...})  — добавить куки в сессию
#   session.headers.update({...})  — добавить заголовки в сессию
#
#   После этого session.get(url) / session.post(url) —
#   всё летит с нужными заголовками и куками автоматически.
#
#   Паттерн для сайтов с авторизацией через куки:
#     1. Открыть DevTools → Application → Cookies
#     2. Скопировать нужные значения в .env
#     3. Загрузить через load_dotenv() + os.environ.get()
#     4. Передать в session.cookies.update()
#

# ───────────────────────────────────────────────────────────────
# ПРИМЕР: Session с куками из .env
# ───────────────────────────────────────────────────────────────

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CUR_DIR, '.env'))

def build_session() -> requests.Session:
    """Создать сессию с заголовками и куками из .env."""
    session = requests.Session()

    session.headers.update({
        'User-Agent': os.environ.get('FT_USER_AGENT', 'Mozilla/5.0'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    session.cookies.update({
        'FTClientSessionId':      os.environ.get('FT_SESSION_ID', ''),
        '__cf_bm':                os.environ.get('FT_CF_BM', ''),
        'ft-access-decision-policy': os.environ.get('FT_ACCESS_POLICY', ''),
    })

    return session


def parse_rss(content: bytes) -> list[dict]:
    """Распарсить RSS-контент в список словарей."""
    soup = BS(content, 'xml')
    result = []
    for item in soup.find_all('item'):
        result.append({
            'title':   item.find('title').get_text(strip=True)       if item.find('title')       else None,
            'link':    item.find('link').get_text(strip=True)         if item.find('link')         else None,
            'pubDate': item.find('pubDate').get_text(strip=True)      if item.find('pubDate')      else None,
            'desc':    item.find('description').get_text(strip=True)  if item.find('description')  else None,
        })
    return result


def safe_get(session: requests.Session, url: str,
             params: dict | None = None, retries: int = 3) -> requests.Response | None:
    """GET с повторами. Возвращает None если все попытки неудачны."""
    for attempt in range(retries):
        try:
            r = session.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r
        except requests.HTTPError:
            if r.status_code == 429:
                time.sleep(2 ** attempt)
            else:
                break
        except requests.RequestException:
            time.sleep(1)
    return None


# Демонстрация: два RSS-эндпоинта
SAVE_DIR = os.path.join(CUR_DIR, 'data')
os.makedirs(SAVE_DIR, exist_ok=True)

session = build_session()

ENDPOINTS = {
    'ft_international': 'https://www.ft.com/rss/home/international',
    'ft_global':        ('https://www.ft.com/global-economy', {'format': 'rss'}),
}

for name, endpoint in ENDPOINTS.items():
    url, params = (endpoint, None) if isinstance(endpoint, str) else endpoint
    r = safe_get(session, url, params=params)
    if r is None:
        print(f"[{name}] не удалось получить данные")
        continue
    items = parse_rss(r.content)
    out = os.path.join(SAVE_DIR, f'{name}.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"[{name}] сохранено {len(items)} новостей → {out}")


# ═══════════════════════════════════════════════════════════════
# ЗАДАЧА 1: Класс FTClient
# ═══════════════════════════════════════════════════════════════
#
# Оберни всё выше в класс FTClient.
#
# Атрибуты:
#   - _session: requests.Session   — создаётся в __init__ через build_session()
#   - save_dir: str                — куда сохранять файлы
#
# Методы:
#   - fetch(endpoint_name: str) -> list[dict]
#       Принимает имя эндпоинта ("international" или "global"),
#       делает запрос через safe_get(), парсит RSS, возвращает список.
#       Если эндпоинт неизвестен — поднять ValueError.
#
#   - save(data: list[dict], filename: str) -> None
#       Сохранить список в save_dir/<filename>.json
#
#   - fetch_and_save(endpoint_name: str) -> int
#       Объединить fetch() + save(). Вернуть количество сохранённых новостей.
#
# Эндпоинты хранить внутри класса как словарь _ENDPOINTS (как выше).
#
# Пример использования:
#   client = FTClient(save_dir='data')
#   count = client.fetch_and_save('international')
#   print(f"Сохранено: {count}")
#


# ── твой код ниже ──────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════
# ЗАДАЧА 2: Обновление куки без перезапуска
# ═══════════════════════════════════════════════════════════════
#
# Куки у FT протухают. Добавь в FTClient метод refresh_cookies().
#
# Метод должен:
#   1. Заново вызвать load_dotenv() с override=True
#      (python-dotenv перечитает .env файл)
#   2. Обновить session.cookies из переменных окружения
#      (те же ключи что в build_session)
#   3. Вернуть dict с новыми значениями куки (для проверки)
#
# Зачем override=True:
#   По умолчанию load_dotenv() не перезаписывает уже установленные
#   переменные окружения. override=True форсирует перечитывание.
#
# Пример использования:
#   client = FTClient(save_dir='data')
#   # ... куки протухли, обновил .env вручную ...
#   new_cookies = client.refresh_cookies()
#   print(new_cookies)
#   count = client.fetch_and_save('international')  # теперь работает


# ── твой код ниже ──────────────────────────────────────────────

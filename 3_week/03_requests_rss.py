# ═══════════════════════════════════════════════════════════════
# ТЕМА: requests — HTTP-запросы и RSS-парсинг
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   requests.get(url) — отправить GET запрос, получить Response.
#   Всегда проверяй статус: r.raise_for_status() бросает исключение
#   при 4xx/5xx — иначе ошибка пройдёт молча.
#
#   r.text      — тело как строка (для HTML, XML)
#   r.content   — тело как байты (для бинарных файлов)
#   r.json()    — тело как dict (только если Content-Type: json)
#   r.status_code — числовой код ответа
#
#   Параметры URL — через params={}:
#     requests.get(url, params={'limit': 10})
#     → url?limit=10   (requests сам кодирует)
#
#   Заголовки — через headers={}:
#     User-Agent нужен когда сервер блокирует без него (код 403).
#     Authorization: Bearer <token> — для API с ключами.
#
#   Session — если делаешь много запросов к одному хосту:
#     session = requests.Session()
#     session.headers.update(headers)  # один раз
#     session.get(url1), session.get(url2)  # переиспользует соединение
#
#   RSS — это XML файл с новостями. Структурированный, без JS.
#   Парсится через BeautifulSoup с парсером 'xml'.
#   Каждая новость = тег <item> с дочерними: title, link, pubDate, description.
#

import requests
import time
from bs4 import BeautifulSoup as BS


# ───────────────────────────────────────────────────────────────
# ПРИМЕР: надёжный GET + парсинг RSS
# ───────────────────────────────────────────────────────────────

def safe_get(url: str, retries: int = 3) -> requests.Response | None:
    """GET с повторами и экспоненциальным backoff при rate limit."""
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            return r
        except requests.HTTPError as e:
            if r.status_code == 429:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
            else:
                break
        except requests.RequestException:
            time.sleep(1)
    return None


def parse_rss(url: str) -> list[dict]:
    """Загрузить RSS-фид и вернуть список новостей."""
    r = safe_get(url)
    if r is None:
        return []

    soup = BS(r.content, 'xml')
    items = []
    for item in soup.find_all('item'):
        title_el   = item.find('title')
        link_el    = item.find('link')
        pubdate_el = item.find('pubDate')
        desc_el    = item.find('description')
        items.append({
            'title':   title_el.get_text(strip=True)   if title_el   else None,
            'link':    link_el.get_text(strip=True)     if link_el    else None,
            'pubDate': pubdate_el.get_text(strip=True)  if pubdate_el else None,
            'desc':    desc_el.get_text(strip=True)[:120] if desc_el  else None,
        })
    return items


# Демонстрация — парсим публичный RSS
TEST_FEED = 'https://feeds.reuters.com/reuters/businessNews'
news = parse_rss(TEST_FEED)
print(f"Получено новостей: {len(news)}")
for n in news[:3]:
    print(f"  [{n['pubDate']}] {n['title']}")

# ═══════════════════════════════════════════════════════════════
# ЗАДАЧА: GET с JSON-ответом и POST-запрос
# ═══════════════════════════════════════════════════════════════
#
# Используем публичный тестовый API: https://httpbin.org
#   GET  /get?param=value   — возвращает JSON с деталями запроса
#   POST /post              — возвращает JSON с телом запроса
#
# Нужно:
#   1. Сделать GET-запрос на https://httpbin.org/get
#      с параметрами: ticker=AAPL, interval=1d
#      Распарсить JSON-ответ через r.json()
#      Вывести значение r.json()['args'] — там будут твои params
#
#   2. Сделать POST-запрос на https://httpbin.org/post
#      с JSON-телом: {"ticker": "MSFT", "action": "buy", "qty": 10}
#      Заголовок Content-Type выставляется автоматически при json={}
#      Вывести r.json()['json'] — там будет твоё тело запроса
#
#   3. Проверить статус-коды обоих ответов через r.status_code
#      и r.raise_for_status() — убедиться что оба вернули 200
#
# Подсказка:
#   requests.get(url, params={'key': 'value'})
#   requests.post(url, json={'key': 'value'})
#

# ── твой код ниже ──────────────────────────────────────────────

import json
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://httpbin.org/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=0',
}

params = {'ticker':'AAPL', 'interval':'1d',}

response = requests.get('https://httpbin.org/get', headers=headers, params=params)

url = response.url
print(f'URL: {url}')

res = response.json()

print(f'interval: {res['args']['interval']}')
print(f'ticker: {res['args']['ticker']}')

params = {"ticker": "MSFT", "action": "buy", "qty": 10}

response = requests.post('https://httpbin.org/post', headers=headers, json=json.dumps(params))
# how to send data= or json=? | if data= then it will be form-encoded, if json= then it will be sent as JSON with the appropriate Content-Type header

print(f'Status code: {response.status_code}')
response.raise_for_status()

print(f'Body of my POST-request: {response.json()['json']}')

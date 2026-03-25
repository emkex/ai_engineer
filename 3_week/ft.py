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

# CUR_DIR = os.path.dirname(os.path.abspath(__file__))
# load_dotenv(os.path.join(CUR_DIR, '.env'))

# def build_session() -> requests.Session:
#     """Создать сессию с заголовками и куками из .env."""
#     session = requests.Session()

#     session.headers.update({
#         'User-Agent': os.environ.get('FT_USER_AGENT', 'Mozilla/5.0'),
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#         'Accept-Language': 'en-US,en;q=0.9',
#     })

#     session.cookies.update({
#         'FTClientSessionId':      os.environ.get('FT_SESSION_ID', ''),
#         '__cf_bm':                os.environ.get('FT_CF_BM', ''),
#         'ft-access-decision-policy': os.environ.get('FT_ACCESS_POLICY', ''),
#     })

#     return session


# def parse_rss(content: bytes) -> list[dict]:
#     """Распарсить RSS-контент в список словарей."""
#     soup = BS(content, 'xml')
#     result = []
#     for item in soup.find_all('item'):
#         result.append({
#             'title':   item.find('title').get_text(strip=True)       if item.find('title')       else None,
#             'link':    item.find('link').get_text(strip=True)         if item.find('link')         else None,
#             'pubDate': item.find('pubDate').get_text(strip=True)      if item.find('pubDate')      else None,
#             'desc':    item.find('description').get_text(strip=True)  if item.find('description')  else None,
#         })
#     return result


# def safe_get(session: requests.Session, url: str,
#              params: dict | None = None, retries: int = 3) -> requests.Response | None:
#     """GET с повторами. Возвращает None если все попытки неудачны."""
#     for attempt in range(retries):
#         try:
#             r = session.get(url, params=params, timeout=10)
#             r.raise_for_status()
#             return r
#         except requests.HTTPError:
#             if r.status_code == 429:
#                 time.sleep(2 ** attempt)
#             else:
#                 break
#         except requests.RequestException:
#             time.sleep(1)
#     return None


# # Демонстрация: два RSS-эндпоинта
# SAVE_DIR = os.path.join(CUR_DIR, 'data')
# os.makedirs(SAVE_DIR, exist_ok=True)

# session = build_session()

# ENDPOINTS = {
#     'ft_international': 'https://www.ft.com/rss/home/international',
#     'ft_global':        ('https://www.ft.com/global-economy', {'format': 'rss'}),
# }

# for name, endpoint in ENDPOINTS.items():
#     url, params = (endpoint, None) if isinstance(endpoint, str) else endpoint
#     r = safe_get(session, url, params=params)
#     if r is None:
#         print(f"[{name}] не удалось получить данные")
#         continue
#     items = parse_rss(r.content)
#     out = os.path.join(SAVE_DIR, f'{name}.json')
#     with open(out, 'w', encoding='utf-8') as f:
#         json.dump(items, f, indent=2, ensure_ascii=False)
#     print(f"[{name}] сохранено {len(items)} новостей → {out}")


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


# ── твой код (исправлен) ────────────────────────────────────────
#
# Что было не так и почему исправлено именно так:
#
# 1. Paths и Session как отдельные классы — лишние сущности.
#    Класс нужен когда есть состояние + несколько методов с ним.
#    Здесь это просто функции → вошли в __init__ FTClient напрямую.
#
# 2. self.requests.Session() — requests это модуль, не атрибут.
#    Правильно: requests.Session()
#
# 3. Paths.CUR_DIR без инстанса — так нельзя, это не classmethod/атрибут класса.
#    __file__ доступен на уровне модуля, взят оттуда напрямую.
#
# 4. session.build_session без () — это ссылка на метод, не его вызов.
#
# 5. @session.setter принимает (self, value) — без value Python не примет.
#    Setter здесь вообще не нужен — session создаётся один раз в __init__.
#
# 6. endpoints.items вместо endpoints.items() — без () это атрибут, не итератор.
#
# 7. return внутри цикла — возвращал после первого эндпоинта.
#    Нужно собирать все результаты и вернуть после цикла.
#
# 8. open(self.stock) где stock = директория — нельзя открыть папку как файл.
#    save принимает имя файла отдельно.

# CUR_DIR = os.path.dirname(os.path.abspath(__file__))
# load_dotenv(os.path.join(CUR_DIR, '.env'))

# class FTClient:

#     _ENDPOINTS = {
#         'ft_international': 'https://www.ft.com/rss/home/international',
#         'ft_global':        ('https://www.ft.com/global-economy', {'format': 'rss'}),
#     }

#     def __init__(self, save_dir: str = 'data'):
#         self.save_dir = os.path.join(CUR_DIR, save_dir)
#         os.makedirs(self.save_dir, exist_ok=True)
#         self._session = self._build_session()

#     def _build_session(self) -> requests.Session:
#         session = requests.Session()
#         session.headers.update({
#             'User-Agent': os.environ.get('FT_USER_AGENT', 'Mozilla/5.0'),
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.9',
#         })
#         session.cookies.update({
#             'FTClientSessionId':         os.environ.get('FT_SESSION_ID', ''),
#             '__cf_bm':                   os.environ.get('FT_CF_BM', ''),
#             'ft-access-decision-policy': os.environ.get('FT_ACCESS_POLICY', ''),
#         })
#         return session

#     def safe_get(self, url: str, params: dict | None = None, retries: int = 3) -> requests.Response | None:
#         for attempt in range(retries):
#             try:
#                 r = self._session.get(url, params=params, timeout=10)
#                 r.raise_for_status()
#                 return r
#             except requests.HTTPError:
#                 if r.status_code == 429:
#                     time.sleep(2 ** attempt)
#                 else:
#                     break
#             except requests.RequestException:
#                 time.sleep(1)
#         return None

#     @staticmethod
#     def parse_rss(content: bytes) -> list[dict]:
#         soup = BS(content, 'xml')
#         result = []
#         for item in soup.find_all('item'):
#             result.append({
#                 'title':   item.find('title').get_text(strip=True)      if item.find('title')      else None,
#                 'link':    item.find('link').get_text(strip=True)        if item.find('link')        else None,
#                 'pubDate': item.find('pubDate').get_text(strip=True)     if item.find('pubDate')     else None,
#                 'desc':    item.find('description').get_text(strip=True) if item.find('description') else None,
#             })
#         return result

#     def fetch(self, endpoint_name: str) -> list[dict]:
#         if endpoint_name not in self._ENDPOINTS:
#             raise ValueError(f"Неизвестный эндпоинт: {endpoint_name}. Доступны: {list(self._ENDPOINTS)}")
#         endpoint = self._ENDPOINTS[endpoint_name]
#         url, params = (endpoint, None) if isinstance(endpoint, str) else endpoint
#         r = self.safe_get(url, params=params)
#         if r is None:
#             print(f"[{endpoint_name}] не удалось получить данные")
#             return []
#         return self.parse_rss(r.content)

#     def save(self, data: list[dict], filename: str) -> None:
#         out = os.path.join(self.save_dir, f'{filename}.json')
#         with open(out, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)

#     def fetch_and_save(self, endpoint_name: str) -> int:
#         data = self.fetch(endpoint_name)
#         if data:
#             self.save(data, endpoint_name)
#         return len(data)


# client = FTClient()
# for name in FTClient._ENDPOINTS:
#     count = client.fetch_and_save(name)
#     print(f"[{name}] сохранено {count} новостей")


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

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CUR_DIR, '.env'))

class FTClient:

    _ENDPOINTS = {
        'ft_international': 'https://www.ft.com/rss/home/international',
        'ft_global':        ('https://www.ft.com/global-economy', {'format': 'rss'}),
    }

    def __init__(self, save_dir: str = 'data'):
        self.save_dir = os.path.join(CUR_DIR, save_dir)
        os.makedirs(self.save_dir, exist_ok=True)
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': os.environ.get('FT_USER_AGENT', 'Mozilla/5.0'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        session.cookies.update({
            'FTClientSessionId':         os.environ.get('FT_SESSION_ID', ''),
            '__cf_bm':                   os.environ.get('FT_CF_BM', ''),
            'ft-access-decision-policy': os.environ.get('FT_ACCESS_POLICY', ''),
        })
        return session

    def refresh_cookies(self):
        """Перечитать .env и обновить куки в сессии (ручной вариант)."""
        load_dotenv(os.path.join(CUR_DIR, '.env'), override=True)
        new_cookies = {
            'FTClientSessionId':         os.environ.get('FT_SESSION_ID', ''),
            '__cf_bm':                   os.environ.get('FT_CF_BM', ''),
            'ft-access-decision-policy': os.environ.get('FT_ACCESS_POLICY', ''),
        }
        self._session.cookies.update(new_cookies)
        return new_cookies

    def refresh_cookies_playwright(self) -> dict:
        """Получить свежие куки через headless-браузер.

        1. Заходит на главную FT
        2. Кликает Accept на GDPR-баннере (если появился)
        3. Если в .env есть FT_EMAIL/FT_PASSWORD — логинится
        4. Собирает все куки домена ft.com → обновляет сессию
        5. Пишет время обновления в data/cookies_meta.json
        """
        from playwright.sync_api import sync_playwright

        email    = os.environ.get('FT_EMAIL', '')
        password = os.environ.get('FT_PASSWORD', '')

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx     = browser.new_context(user_agent=os.environ.get('FT_USER_AGENT', 'Mozilla/5.0'))
            page    = ctx.new_page()

            page.goto('https://www.ft.com/', wait_until='networkidle')

            # GDPR consent banner — кликаем Accept если появился.
            # Если клик не сработал — передаём управление MCP Playwright агенту:
            # он сам сделает snapshot страницы, найдёт актуальный селектор и починит код.
            # Баннер находится в iframe[title="SP Consent Message"] (consent-manager.ft.com)
            consent_clicked = False
            try:
                page.locator('iframe[title="SP Consent Message"]') \
                    .content_frame \
                    .get_by_role('button', name='Accept') \
                    .click(timeout=5000)
                page.wait_for_load_state('networkidle')
                consent_clicked = True
            except Exception:
                pass

            if consent_clicked:
                print("  [playwright] consent banner: нажат")
            else:
                print("  [playwright] consent banner: не появился (норма)")

            if email and password:
                page.goto('https://accounts.ft.com/login', wait_until='networkidle')
                page.fill('input[type="email"]',    email)
                page.fill('input[type="password"]', password)
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')

            raw = ctx.cookies()
            browser.close()

        fresh = {c['name']: c['value'] for c in raw if 'ft.com' in c.get('domain', '')}
        self._session.cookies.update(fresh)

        # записываем время обновления в meta-файл (не в .env)
        meta_path = os.path.join(self.save_dir, 'cookies_meta.json')
        meta = {'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'), 'cookies_count': len(fresh)}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)

        return fresh

    def _load_seen_links(self, filename: str, limit: int = 500) -> set:
        """Загрузить только ссылки из последних limit новостей для дедупликации."""
        out = os.path.join(self.save_dir, f'{filename}.json')
        if not os.path.exists(out):
            return set()
        with open(out, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # берём хвост — свежие новости, дубли обычно там
        return {item['link'] for item in data[-limit:] if item.get('link')}

    def _purge_old(self, filename: str, months: int = 6) -> int:
        """Удалить новости старше months месяцев. Возвращает кол-во удалённых."""
        out = os.path.join(self.save_dir, f'{filename}.json')
        if not os.path.exists(out):
            return 0
        with open(out, 'r', encoding='utf-8') as f:
            data = json.load(f)

        from datetime import datetime, timezone
        cutoff = datetime.now(timezone.utc).timestamp() - months * 30 * 86400

        def is_fresh(item: dict) -> bool:
            pub = item.get('pubDate', '')
            if not pub:
                return True  # нет даты — не удаляем
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub)
                return dt.timestamp() > cutoff
            except Exception:
                return True  # не распарсили — не удаляем

        fresh = [item for item in data if is_fresh(item)]
        removed = len(data) - len(fresh)
        if removed:
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(fresh, f, indent=2, ensure_ascii=False)
        return removed

    def safe_get(self, url: str, params: dict | None = None, retries: int = 3) -> requests.Response | None:
        for attempt in range(retries):
            try:
                r = self._session.get(url, params=params, timeout=10)
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

    @staticmethod
    def parse_rss(content: bytes) -> list[dict]:
        soup = BS(content, 'xml')
        result = []
        for item in soup.find_all('item'):
            result.append({
                'title':   item.find('title').get_text(strip=True)      if item.find('title')      else None,
                'link':    item.find('link').get_text(strip=True)        if item.find('link')        else None,
                'pubDate': item.find('pubDate').get_text(strip=True)     if item.find('pubDate')     else None,
                'desc':    item.find('description').get_text(strip=True) if item.find('description') else None,
            })
        return result

    def fetch(self, endpoint_name: str) -> list[dict]:
        if endpoint_name not in self._ENDPOINTS:
            raise ValueError(f"Неизвестный эндпоинт: {endpoint_name}. Доступны: {list(self._ENDPOINTS)}")
        endpoint = self._ENDPOINTS[endpoint_name]
        url, params = (endpoint, None) if isinstance(endpoint, str) else endpoint
        r = self.safe_get(url, params=params)
        if r is None:
            print(f"[{endpoint_name}] не удалось получить данные")
            return []
        return self.parse_rss(r.content)

    def save(self, data: list[dict], filename: str) -> int:
        """Дозаписать только новые новости. Дубли по ссылке пропускаются."""
        out      = os.path.join(self.save_dir, f'{filename}.json')
        seen     = self._load_seen_links(filename)
        new_items = [item for item in data if item.get('link') not in seen]
        if not new_items:
            return 0
        # дозапись: читаем полный файл только если есть что добавить
        existing = []
        if os.path.exists(out):
            with open(out, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(existing + new_items, f, indent=2, ensure_ascii=False)
        return len(new_items)

    def fetch_and_save(self, endpoint_name: str) -> int:
        data = self.fetch(endpoint_name)
        if not data:
            return 0
        return self.save(data, endpoint_name)

    def run_loop(self, interval_min: int = 30) -> None:
        """Бесконечный цикл: обновляет куки, собирает новости, чистит старые (раз в сутки)."""
        print(f"Запуск цикла, интервал {interval_min} мин. Ctrl+C для остановки.")
        last_purge = 0.0

        while True:
            print(f"\n[{time.strftime('%H:%M:%S')}] Обновляю куки...")
            self.refresh_cookies_playwright()

            for name in self._ENDPOINTS:
                new_count = self.fetch_and_save(name)
                print(f"  [{name}] +{new_count} новых")

            # автоочистка старых новостей — раз в сутки
            if time.time() - last_purge > 86400:
                for name in self._ENDPOINTS:
                    removed = self._purge_old(name, months=6)
                    if removed:
                        print(f"  [{name}] удалено {removed} старых новостей")
                last_purge = time.time()

            print(f"  Следующий запуск через {interval_min} мин.")
            time.sleep(interval_min * 60)


client = FTClient()
client.run_loop(interval_min=30)

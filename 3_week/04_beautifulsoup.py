# ═══════════════════════════════════════════════════════════════
# ТЕМА: BeautifulSoup — парсинг HTML
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   BS(content, 'html.parser') — создать объект из HTML-строки/байтов.
#   Два парсера: 'html.parser' (стандартный), 'lxml' (быстрее, pip install lxml).
#   Для RSS/XML — 'xml'.
#
#   Поиск элементов:
#     soup.select_one('.class')   — первый элемент по CSS-селектору
#     soup.select('.class')       — все → список
#     soup.find('tag')            — первый тег
#     soup.find_all('tag')        — все → список
#
#   Извлечение данных:
#     el.get_text(strip=True)     — текст без пробелов по краям
#     el.get('href')              — атрибут безопасно (None если нет)
#     el['href']                  — атрибут напрямую (KeyError если нет)
#     el['class']                 → список! не строка
#
#   Навигация по дереву:
#     el.parent                   — родительский элемент
#     el.find('span')             — поиск внутри элемента
#
#   Паттерн "список карточек → данные":
#     for card in soup.select('.card'):
#         title = card.select_one('h2')
#         if not title: continue   # защита от None
#         results.append({'title': title.get_text(strip=True)})
#
#   Паттерн "таблица → список словарей":
#     headers = [th.get_text(strip=True) for th in table.select('th')]
#     for tr in table.select('tbody tr'):
#         cells = [td.get_text(strip=True) for td in tr.select('td')]
#         rows.append(dict(zip(headers, cells)))
#
#   ВАЖНО: BS работает только со статичным HTML.
#   Если данные подгружаются через JS — нужен Playwright.
#   Сначала проверь Ctrl+U (исходник страницы) — есть ли данные там.
#

import requests
from bs4 import BeautifulSoup as BS


# ───────────────────────────────────────────────────────────────
# ПРИМЕР: парсинг HTML-таблицы с котировками
# ───────────────────────────────────────────────────────────────

# Имитируем HTML который мог бы прийти со страницы котировок
SAMPLE_HTML = """
<html><body>
<h1>Market Overview</h1>
<table class="quotes-table">
  <thead>
    <tr><th>Ticker</th><th>Price</th><th>Change</th><th>Volume</th></tr>
  </thead>
  <tbody>
    <tr>
      <td class="ticker">AAPL</td>
      <td class="price">$182.50</td>
      <td class="change positive">+1.2%</td>
      <td>54,200,100</td>
    </tr>
    <tr>
      <td class="ticker">MSFT</td>
      <td class="price">$415.20</td>
      <td class="change positive">+0.8%</td>
      <td>22,100,400</td>
    </tr>
    <tr>
      <td class="ticker">TSLA</td>
      <td class="price">$175.40</td>
      <td class="change negative">-2.1%</td>
      <td>97,300,000</td>
    </tr>
  </tbody>
</table>
<div class="news-feed">
  <div class="news-item">
    <h3 class="headline"><a href="/news/1">Fed holds rates steady amid inflation concerns</a></h3>
    <span class="source">Reuters</span>
    <span class="time">2h ago</span>
  </div>
  <div class="news-item">
    <h3 class="headline"><a href="/news/2">Tech stocks rally on strong earnings</a></h3>
    <span class="source">Bloomberg</span>
    <span class="time">4h ago</span>
  </div>
  <div class="news-item">
    <h3 class="headline"><a href="/news/3">Oil prices drop as OPEC signals output increase</a></h3>
    <span class="source">FT</span>
    <span class="time">6h ago</span>
  </div>
</div>
</body></html>
"""

soup = BS(SAMPLE_HTML, 'html.parser')

# Паттерн: таблица → список словарей
table = soup.select_one('table.quotes-table')
headers = [th.get_text(strip=True) for th in table.select('th')]
quotes = []
for tr in table.select('tbody tr'):
    cells = [td.get_text(strip=True) for td in tr.select('td')]
    quotes.append(dict(zip(headers, cells)))

print("Котировки:")
for q in quotes:
    print(f"  {q['Ticker']} — {q['Price']} ({q['Change']})")

# Паттерн: список карточек → данные
print("\nПоследние новости:")
for item in soup.select('.news-item'):
    headline = item.select_one('.headline a')
    source   = item.select_one('.source')
    if not headline:
        continue
    print(f"  [{source.get_text(strip=True)}] {headline.get_text(strip=True)}")


# ═══════════════════════════════════════════════════════════════
# ЗАДАЧА: Парсинг страницы с активами
# ═══════════════════════════════════════════════════════════════
#
# Ниже — HTML с двумя секциями: таблица активов и список событий.
# Это типичная структура страницы агрегатора котировок.
#
# Нужно:
#   1. Создать объект BeautifulSoup из TASK_HTML
#
#   2. Распарсить таблицу с классом "assets-table":
#        - извлечь заголовки из <th>
#        - для каждой строки <tr> в <tbody> собрать словарь
#          { заголовок: значение ячейки }
#        - сохранить в список assets
#
#   3. Из списка assets:
#        - найти актив с максимальной ценой (поле Price — строка "$XXX",
#          нужно убрать $ и привести к float)
#        - найти все активы где Change содержит "-" (падающие)
#        - вывести оба результата
#
#   4. Распарсить блок событий (.event-list .event-item):
#        - извлечь: title (тег h4), category (span.category), impact (span.impact)
#        - собрать в список events
#        - вывести только события с impact == "HIGH"
#
# Подсказка для шага 3:
#   price_str = asset['Price']  # "$875.40"
#   price = float(price_str.replace('$', '').replace(',', ''))
#

TASK_HTML = """
<html><body>
<table class="assets-table">
  <thead>
    <tr><th>Ticker</th><th>Name</th><th>Price</th><th>Change</th><th>Sector</th></tr>
  </thead>
  <tbody>
    <tr><td>NVDA</td><td>NVIDIA Corp.</td><td>$875.40</td><td>+3.2%</td><td>Technology</td></tr>
    <tr><td>GOLD</td><td>Barrick Gold</td><td>$17.85</td><td>-0.5%</td><td>Commodities</td></tr>
    <tr><td>SPY</td><td>S&amp;P 500 ETF</td><td>$521.10</td><td>+0.4%</td><td>ETF</td></tr>
    <tr><td>TLT</td><td>20yr Bond ETF</td><td>$92.15</td><td>-1.1%</td><td>Bonds</td></tr>
    <tr><td>BTC</td><td>Bitcoin USD</td><td>$67,400.00</td><td>+2.8%</td><td>Crypto</td></tr>
    <tr><td>XOM</td><td>ExxonMobil</td><td>$112.30</td><td>-0.3%</td><td>Energy</td></tr>
  </tbody>
</table>

<div class="event-list">
  <div class="event-item">
    <h4>Fed Rate Decision</h4>
    <span class="category">Monetary Policy</span>
    <span class="impact">HIGH</span>
  </div>
  <div class="event-item">
    <h4>NVDA Earnings Report</h4>
    <span class="category">Corporate</span>
    <span class="impact">HIGH</span>
  </div>
  <div class="event-item">
    <h4>US PMI Data Release</h4>
    <span class="category">Macro</span>
    <span class="impact">MEDIUM</span>
  </div>
  <div class="event-item">
    <h4>OPEC Monthly Report</h4>
    <span class="category">Commodities</span>
    <span class="impact">HIGH</span>
  </div>
  <div class="event-item">
    <h4>EU CPI Flash Estimate</h4>
    <span class="category">Macro</span>
    <span class="impact">MEDIUM</span>
  </div>
</div>
</body></html>
"""


# ── твой код ниже ──────────────────────────────────────────────

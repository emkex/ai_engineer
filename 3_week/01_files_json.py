# ═══════════════════════════════════════════════════════════════
# ТЕМА: Файлы и JSON
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   Работа с файлами — всегда через `with open(path, mode)`.
#   Файл закрывается автоматически, даже если возникнет ошибка.
#
#   Режимы:
#     'r'  — читать (по умолчанию)
#     'w'  — писать (ЗАТИРАЕТ файл если существует)
#     'a'  — дописывать в конец
#     'rb' / 'wb' — бинарный режим (для картинок, моделей и т.д.)
#
#   JSON — это просто строка определённого формата.
#   Python-словарь и JSON-строка — это разные вещи!
#
#     json.dumps(obj)    # dict → str  (в память)
#     json.loads(s)      # str  → dict (из памяти)
#     json.dump(obj, f)  # dict → файл
#     json.load(f)       # файл → dict
#
#   JSON поддерживает только: dict, list, str, int, float, bool, None
#   datetime, set, numpy — нужна конвертация перед сохранением
#
#   Пути — всегда через os.path.join(), не склеивать строками:
#     os.path.join("data", "raw_feed.json")  # правильно
#     "data" + "/" + "raw_feed.json"         # хрупко (Windows / Linux)
#

import json
import os

# ───────────────────────────────────────────────────────────────
# ПРИМЕР: загрузить JSON, нормализовать, сохранить
# ───────────────────────────────────────────────────────────────
# Допустим, API вернул нам список позиций.
# Некоторые поля могут быть None — нужно заполнить значениями по умолчанию.

RAW_DATA = [
    {"ticker": "NVDA", "name": "NVIDIA Corp.", "price": 875.40, "change_pct": 2.15},
    {"ticker": "TSLA", "name": None,           "price": 175.40, "change_pct": None},
    {"ticker": "BTC",  "name": "Bitcoin USD",  "price": 67400,  "change_pct": -1.30},
]

# Шаг 1: нормализуем — None → значение по умолчанию
def normalize(record: dict) -> dict:
    return {
        "ticker":     record["ticker"],
        "name":       record["name"] if record["name"] is not None else "N/A",
        "price":      record["price"],
        "change_pct": record["change_pct"] if record["change_pct"] is not None else 0.0,
    }

clean = [normalize(r) for r in RAW_DATA]

# Шаг 2: сохраняем в файл
output_path = os.path.join("3_week", "data", "example_clean.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(clean, f, ensure_ascii=False, indent=2)

print(f"Сохранено {len(clean)} записей → {output_path}")

# Шаг 3: читаем обратно и убеждаемся
with open(output_path, "r", encoding="utf-8") as f:
    loaded = json.load(f)

print(f"Прочитано обратно: {len(loaded)} записей")
for item in loaded:
    print(f"  {item['ticker']}: ${item['price']}, change={item['change_pct']}%")


# ═══════════════════════════════════════════════════════════════
# ЗАДАЧА 1: Фид инструментов
# ═══════════════════════════════════════════════════════════════
#
# В файле  data/raw_feed.json  лежит JSON с 12 записями.
# Каждая запись: ticker, name, price, volume, sector
# Некоторые поля — null, некоторые volume == 0.
#
# Нужно:
#   1. Прочитать файл data/raw_feed.json через json.load()
#
#   2. Нормализовать каждую запись:
#        - name == null  → "Unknown"
#        - volume == null → 0
#
#   3. Отфильтровать записи где volume == 0 (нет торгов — не нужны)
#
#   4. Сохранить отфильтрованный список в  data/clean_feed.json
#      с отступами indent=2 и ensure_ascii=False
#
#   5. Перечитать data/clean_feed.json обратно.
#      Вывести:
#        - количество оставшихся записей
#        - суммарный volume по всем записям
#        - тикер с максимальной ценой
#
# Ожидаемый вывод (значения могут отличаться):
#   Записей после фильтрации: 8
#   Суммарный объём: 330 000 000
#   Самый дорогой: NVDA ($875.40)
#


# ── твой код ниже ──────────────────────────────────────────────

import json
import os

# ОШИБКА 1: пути — скрипт запускается из корня репозитория, поэтому
# 'data/raw_feed.json' не найдёт файл. Нужно строить путь относительно
# расположения самого скрипта через __file__.
BASE_DIR = os.path.dirname(__file__)  # папка 3_week/
DATA_DIR = os.path.join(BASE_DIR, "data")

with open(os.path.join(DATA_DIR, "raw_feed.json"), "r", encoding="utf-8") as fp:
    loaded_response = json.load(fp)


def normalize(line: dict) -> dict:
    return {
        "ticker": line["ticker"],
        "name":   line["name"]   if line["name"]   is not None else "Unknown",
        "price":  line["price"],
        "volume": line["volume"] if line["volume"] is not None else 0,
        "sector": line["sector"],
    }


# ОШИБКА 2: логика поиска максимальной цены была неверной —
# init не обновлялся, поэтому max_price_ticker всегда перезаписывался
# на каждый элемент (не искал реальный максимум).
# Исправление: обновлять init до текущей цены при нахождении нового максимума.

# ОШИБКА 3: запись в JSON построчно через 'a' + json.dump() внутри цикла
# создаёт невалидный JSON — несколько объектов подряд без обёртки в список.
# Правильно: собрать отфильтрованный список и сохранить одним json.dump().

tot_vol = 0
max_price = 0
max_price_ticker = None
clean = []

for record in loaded_response:
    record = normalize(record)

    if record["price"] > max_price:
        max_price = record["price"]          # обновляем текущий максимум
        max_price_ticker = record["ticker"]

    if record["volume"] == 0:
        continue

    tot_vol += record["volume"]
    clean.append(record)

# ОШИБКА 4: json.dump(line, f, ...) — переменная f не существует в этом scope.
# Была опечатка: файл открывался как fpp, а передавался f.
# Теперь это не проблема — пишем одним вызовом после цикла.
with open(os.path.join(DATA_DIR, "clean_feed.json"), "w", encoding="utf-8") as f:
    json.dump(clean, f, ensure_ascii=False, indent=2)

with open(os.path.join(DATA_DIR, "clean_feed.json"), "r", encoding="utf-8") as f:
    res = json.load(f)

print(f"Записей после фильтрации: {len(res)}")
print(f"Суммарный объём: {tot_vol:,}")
print(f"Самый дорогой: {max_price_ticker} (${max_price:.2f})")

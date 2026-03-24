# ═══════════════════════════════════════════════════════════════
# ТЕМА: CSV и потоки
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   CSV — текстовый формат, каждая строка = одна запись,
#   поля разделены запятой. Первая строка обычно — заголовки.
#
#   Для аналитики — pd.read_csv() / df.to_csv(), pandas делает всё.
#   Модуль csv — только если pandas избыточен или нужен ручной контроль.
#
#   Дозапись в CSV без pandas:
#     with open(path, 'a', newline='') as f:
#         writer = csv.DictWriter(f, fieldnames=[...])
#         writer.writerow({...})
#   ВАЖНО: newline='' — иначе Windows вставит лишние пустые строки.
#
#   Потоки:
#     Поток = последовательность байтов + текущая позиция.
#     Читать большой файл построчно:
#       for line in f:   # НЕ f.readlines() — не грузит весь файл в память
#           process(line)
#
#     Потоковое чтение нужно когда:
#       - файл больше доступной RAM
#       - данные приходят частями (HTTP streaming, LLM-токены)
#       - лог пишется непрерывно (режим 'a')
#

import csv
import os
import pandas as pd
from datetime import datetime, timedelta
import random

# ───────────────────────────────────────────────────────────────
# ПРИМЕР: сгенерировать события, сохранить в CSV, прочитать
# ───────────────────────────────────────────────────────────────

random.seed(42)

TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "BTC"]
EVENT_TYPES = ["signal", "alert", "info"]

# генерируем 15 событий
base_time = datetime(2025, 3, 1, 9, 30)
events = []
for i in range(15):
    events.append({
        "timestamp":  (base_time + timedelta(minutes=i * 7)).isoformat(),
        "ticker":     random.choice(TICKERS),
        "event_type": random.choice(EVENT_TYPES),
        "value":      round(random.uniform(-5.0, 5.0), 4),
    })

# сохраняем через pandas
example_path = os.path.join("3_week", "data", "example_events.csv")
df = pd.DataFrame(events)
df.to_csv(example_path, index=False)
print(f"Сохранено {len(df)} событий → {example_path}")

# читаем обратно и считаем статистику
df2 = pd.read_csv(example_path)
print("\nКоличество по типам:")
print(df2["event_type"].value_counts().to_string())
print("\nСредний value по типам:")
print(df2.groupby("event_type")["value"].mean().round(4).to_string())

# дозаписываем 3 строки через csv (без pandas)
extra = [
    {"timestamp": "2024-03-01T11:00:00", "ticker": "ETH", "event_type": "alert", "value": 1.23},
    {"timestamp": "2024-03-01T11:07:00", "ticker": "SPY", "event_type": "signal", "value": -0.87},
    {"timestamp": "2024-03-01T11:14:00", "ticker": "GLD", "event_type": "info",   "value": 0.05},
]
with open(example_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp", "ticker", "event_type", "value"])
    writer.writerows(extra)

df3 = pd.read_csv(example_path)
print(f"\nПосле дозаписи: {len(df3)} строк (было {len(df2)})")


# ═══════════════════════════════════════════════════════════════
# ЗАДАЧА 2: Журнал торговых сигналов
# ═══════════════════════════════════════════════════════════════
#
# Нужно:
#   1. Сгенерировать список из 25 событий — словарей:
#        timestamp  — datetime с шагом 10 минут начиная с 2024-06-01 09:30
#        ticker     — случайный из ["AAPL","MSFT","NVDA","TSLA","BTC","ETH","SPY"]
#        event_type — случайный из ["signal", "alert", "info"]
#        value      — случайный float в диапазоне [-3.0, 3.0], округлить до 4 знаков
#        confidence — случайный float в диапазоне [0.5, 1.0], округлить до 2 знаков
#      (поле confidence — новое, в примере его нет)
#
#   2. Сохранить в  data/signals_log.csv  через pandas (index=False)
#
#   3. Перечитать CSV через pandas. Вывести:
#        - топ-3 тикера по количеству событий
#        - средний confidence для каждого event_type
#        - количество событий с confidence > 0.8
#
#   4. Дозаписать в тот же файл ещё 5 новых событий
#      через модуль csv (НЕ pandas, режим 'a')
#      Данные придумай сам — главное структура та же.
#
#   5. Перечитать файл ещё раз и проверить:
#        - итоговое количество строк == 30
#        - все поля на месте (нет NaN в важных колонках)
#
# Подсказка: для шага 4 не забудь newline='' в open()
# и не пиши заголовки повторно (header=False у DictWriter
# или просто writer.writerows() без writeheader())
#


# ── твой код ниже ──────────────────────────────────────────────

import os
os.chdir('/home/emkex/life/capital/areas/code/ai_engineer')


import csv
import os
import pandas as pd
from datetime import datetime, timedelta
import random

random.seed(42)

#generate 25 events
TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "BTC", "ETH", "SPY"]
EVENT_TYPES = ["signal", "alert", "info"]
base_time = datetime(2024, 6, 1, 9, 30)
events = []
for i in range(25):
    events.append({
        "timestamp":  (base_time + timedelta(minutes=i * 10)).isoformat(),
        "ticker":     random.choice(TICKERS),
        "event_type": random.choice(EVENT_TYPES),
        "value":      round(random.uniform(-3.0, 3.0), 4),
        "confidence": round(random.uniform(0.5, 1.0), 2),
    })

#save to csv
output_path = os.path.join("3_week", "data", "signals_log.csv")
df = pd.DataFrame(events)
df.to_csv(output_path, index=False)
print(f"Сохранено {len(df)} событий → {output_path}")

events_res = pd.read_csv(output_path)

print(events_res)

# #top-3 tickers by event count
print("\nТоп-3 тикера по количеству событий:")
print(events_res["ticker"].value_counts().head(3).to_string())

# #average confidence by event_type
print("\nСредний confidence для каждого event_type:")
print(events_res.groupby('event_type')['confidence'].mean().round(2).to_string())

# количество событий с confidence > 0.8
print("\nКоличество событий с confidence > 0.8: ")
print((events_res['confidence'] > 0.8).sum())

next_events = []

for i in range(5):
    next_events.append({
        "timestamp":  (base_time + timedelta(minutes=500 + i * 10)).isoformat(),
        "ticker":     random.choice(TICKERS),
        "event_type": random.choice(EVENT_TYPES),
        "value":      round(random.uniform(-3.0, 3.0), 4),
        "confidence": round(random.uniform(0.5, 1.0), 2),
    })

with open(output_path, 'a', newline='', encoding='utf-8') as fp:
    writer = csv.DictWriter(fp, fieldnames=["timestamp", "ticker", "event_type", "value", "confidence"])
    writer.writerows(next_events)

# reread and все поля на месте (нет NaN в важных колонках)

with open(output_path, 'r', encoding='utf-8') as fpp:
    reader = csv.reader(fpp)
    rows = list(reader)
    print(f"\nИтоговое количество строк: {len(rows)} (ожидаем 30)")
    for row in rows[1:]:  # Skip header
        if any(field == '' for field in row):
            print("Ошибка: найдены пустые поля в строке:", row)
            break
    else:
        print("Проверка пройдена: все поля заполнены.")

# or

df4 = pd.read_csv(output_path)
print(f"\nПосле дозаписи: {len(df4)} строк (было {len(events_res)})")
if df4.isnull().values.any():
    print("Ошибка: найдены NaN в данных.")
else:
    print("Проверка пройдена: NaN не обнаружены.")


import numpy as np  # импорт NumPy для случайных данных
import pandas as pd  # импорт pandas для работы с данными
import matplotlib.pyplot as plt  # импорт matplotlib для визуализации
from datetime import datetime, timedelta  # импорт datetime для базовых операций с датами

from pandas.tseries.offsets import MonthEnd  # импорт смещения месяца

dates = pd.date_range("2020-01-01", periods=10, freq="D")  # создание диапазона дат с частотой день
ts = pd.Series(np.random.standard_normal(10), index=dates)  # создание временного ряда с случайными данными
print(ts)  # вывод временного ряда

now = datetime.now()  # текущая дата и время
delta = now - datetime(2020, 1, 1)  # разница во времени
print(delta.days)  # количество дней в дельте

stamp = datetime(2020, 1, 1)  # создание datetime объекта
str_stamp = stamp.strftime("%Y-%m-%d")  # форматирование в строку
print(str_stamp)  # вывод форматированной даты

parsed = pd.to_datetime("2020-01-01")  # парсинг строки в datetime
print(parsed)  # вывод распарсенной даты

print(ts["2020-01-03"])  # индексация по дате
dup_dates = pd.DatetimeIndex(["2020-01-01", "2020-01-01", "2020-01-02"])  # дублирующиеся даты
dup_ts = pd.Series([1, 2, 3], index=dup_dates)  # ряд с дубликатами
print(dup_ts.groupby(level=0).mean())  # агрегация по уровню индекса

freq_range = pd.date_range("2020-01-01", periods=5, freq="2H")  # диапазон с частотой 2 часа
print(freq_range)  # вывод диапазона

shifted = ts.shift(2)  # сдвиг данных на 2 периода
print(shifted)  # вывод сдвинутого ряда

end_of_month = MonthEnd().rollforward(datetime(2020, 5, 15))  # сдвиг к концу месяца
print(end_of_month)  # вывод конца месяца

tz_ts = ts.tz_localize("UTC")  # локализация в UTC
print(tz_ts)  # вывод с часовым поясом

converted = tz_ts.tz_convert("Europe/Moscow")  # конвертация в другой пояс
print(converted)  # вывод конвертированного

period = pd.Period("2020", freq="A-DEC")  # создание годичного периода
print(period + 1)  # сдвиг периода на 1 год

period_range = pd.period_range("2020-01", "2020-06", freq="M")  # диапазон месячных периодов
print(period_range)  # вывод диапазона периодов

period_ts = ts.to_period("M")  # конвертация в периоды
print(period_ts)  # вывод в периодах

timestamp_back = period_ts.to_timestamp()  # обратно в timestamps
print(timestamp_back)  # вывод обратно

resampled_mean = ts.resample("5D").mean()  # понижающая передискретизация со средним
print(resampled_mean)  # вывод среднего по 5 дням

ohlc = ts.resample("5D", label='left').ohlc()  # OHLC агрегация
print(ohlc)  # вывод OHLC

upsampled = ts.resample("T").ffill()  # повышающая с заполнением
print(upsampled)  # вывод заполненного

group_resample = ts.resample("M").sum()  # группировка и сумма по месяцам
print(group_resample)  # вывод суммы

# ----------------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import percentileofscore

np.random.seed(42)
dates = pd.date_range("2020-01-01", periods=1500, freq="B")
prices = 100 + np.cumsum(np.random.randn(1500) * 0.8)
close = pd.Series(prices, index=dates)

daily_ret = close.pct_change().dropna()  # дневные доходности
close_ewm = close.ewm(span=250).mean()  # экспоненциальное! скользящее среднее доходностей

# скользящая 250-дневная волатильность
vol_rolling = daily_ret.rolling(250, min_periods=10).std()

# расширяющееся среднее волатильности
vol_expanding_mean = vol_rolling.expanding().mean()

# функция для 2% ранга
def score_at_2percent(x):
    return percentileofscore(x, 0.01)

# расчёт 2%-го процентильного ранга по доходностям
percentile_2pct = daily_ret.rolling(250).apply(score_at_2percent)

# обрезаем начало для чистоты (первые 100 точек шумные)
START_AFTER = 200
daily_ret_clean = daily_ret.iloc[START_AFTER:]
vol_rolling_clean = vol_rolling.iloc[START_AFTER:]
vol_expanding_clean = vol_expanding_mean.iloc[START_AFTER:]
percentile_clean = percentile_2pct.iloc[START_AFTER:]

# график цен
plt.figure(figsize=(12, 6))
plt.plot(close, label='AAPL Close Price', color='blue')
plt.plot(close_ewm, label='EWMA of Close Price', color='orange', alpha=0.7)
plt.title('AAPL Close Price (имитация)')
plt.xlabel('Дата')
plt.ylabel('Цена, $')
plt.grid(alpha=0.3)
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('aapl_close_price.png')
plt.show()

# график волатильности
plt.figure(figsize=(12, 6))
plt.plot(vol_rolling_clean, label='Rolling Volatility (250d)', color='blue')
plt.plot(vol_expanding_clean, label='Expanding Mean Vol', color='orange')
# plt.plot(percentile_clean / 100, label='2% Percentile Rank (масштаб 0-1)', color='green', alpha=0.7)
plt.title('Volatility + 2% Percentile Rank')
plt.xlabel('Дата')
plt.ylabel('Значение')
plt.grid(alpha=0.3)
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('volatility_percentile_rank.png')
plt.show()

# график  + 2% ранг
plt.figure(figsize=(12, 6))
plt.plot(percentile_clean, label='1% Percentile Rank (масштаб 0-100)', color='green', alpha=0.7)
plt.title('1% Percentile Rank') # проценты движения меньше n% True, график покажет, насколько часто были такие движения (а не больше n%), например, 90% === 90% движений были меньше n%
plt.xlabel('Дата')
plt.ylabel('Значение')
plt.grid(alpha=0.3)
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('percentile_rank.png')
plt.show()
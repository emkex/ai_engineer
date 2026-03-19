# ═══════════════════════════════════════════════════════════════
# ТЕМА 6: dataclass — современный способ писать классы
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   @dataclass автоматически генерирует: __init__, __repr__, __eq__
#   Это убирает огромный бойлерплейт при создании классов-данных.
#
#   from dataclasses import dataclass, field
#
#   @dataclass               — базовый вариант
#   @dataclass(order=True)   — добавляет __lt__, __le__, __gt__, __ge__
#   @dataclass(frozen=True)  — неизменяемый объект (immutable), hashable
#   @dataclass(eq=False)     — не генерировать __eq__
#
#   field() — тонкая настройка поля:
#     field(default=0)                       — значение по умолчанию
#     field(default_factory=list)            — фабрика (для мутабельных типов!)
#     field(repr=False)                      — скрыть из repr
#     field(compare=False)                   — исключить из сравнения
#     field(init=False)                      — не включать в __init__
#
#   __post_init__(self) — вызывается после __init__, для валидации.
#
#   ClassVar[T] — атрибут класса, не экземпляра (не попадает в __init__)
#
# ───────────────────────────────────────────────────────────────
# ПРИМЕР 1: Базовый dataclass
# ───────────────────────────────────────────────────────────────

from dataclasses import dataclass, field, asdict, astuple
from datetime import datetime
from typing import ClassVar


@dataclass(order=True)
class Peak:
    """Хроматографический пик."""
    retention_time: float       # время удерживания (мин) — используется для сортировки
    intensity: float
    compound_name: str = ""
    is_confirmed: bool = False

    def area(self) -> float:
        """Приближённая площадь пика (трапеция)."""
        return self.intensity * 0.5  # упрощение


peaks = [
    Peak(5.2, 1200.0, "Кофеин", True),
    Peak(2.1, 800.0, "Глюкоза"),
    Peak(8.7, 2500.0, "Аспирин", True),
    Peak(3.4, 450.0),
]

# Благодаря order=True — автоматическая сортировка по retention_time
peaks_sorted = sorted(peaks)
print("Пики по времени удерживания:")
for p in peaks_sorted:
    print(f"  {p.retention_time:.1f} мин — {p.compound_name or 'неизвестно'}: {p.intensity}")


# ───────────────────────────────────────────────────────────────
# ПРИМЕР 2: __post_init__ и field(default_factory)
# ───────────────────────────────────────────────────────────────

@dataclass
class ChromatogramResult:
    """Результат хроматографического анализа."""

    sample_id: str
    method: str
    timestamp: datetime = field(default_factory=datetime.now)
    peaks: list[Peak] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    _peak_count: int = field(init=False, repr=False)  # вычисляется в __post_init__

    # ClassVar — счётчик всех созданных результатов (не в __init__)
    total_results: ClassVar[int] = 0

    def __post_init__(self) -> None:
        # валидация после инициализации
        if not self.sample_id.strip():
            raise ValueError("sample_id не может быть пустым")
        if self.method not in ("ВЭЖХ", "ГХ", "ИСП-МС", "КЭ"):
            raise ValueError(f"Неизвестный метод: {self.method}")
        self._peak_count = len(self.peaks)
        ChromatogramResult.total_results += 1

    def add_peak(self, peak: Peak) -> None:
        self.peaks.append(peak)
        self._peak_count += 1

    def summary(self) -> str:
        confirmed = sum(1 for p in self.peaks if p.is_confirmed)
        return (f"[{self.sample_id}] метод={self.method}, "
                f"пиков={len(self.peaks)}, подтверждено={confirmed}")


r1 = ChromatogramResult("S-001", "ВЭЖХ")
r1.add_peak(peaks[0])
r1.add_peak(peaks[2])

r2 = ChromatogramResult("S-002", "ГХ", peaks=[peaks[1]])

print(f"\n{r1}")
print(r1.summary())
print(f"Всего результатов: {ChromatogramResult.total_results}")

# Ошибка валидации
try:
    bad = ChromatogramResult("", "ВЭЖХ")
except ValueError as e:
    print(f"Ошибка: {e}")


# ───────────────────────────────────────────────────────────────
# ПРИМЕР 3: frozen=True — неизменяемый объект
# ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class IsotopeRatio:
    """Изотопное соотношение — неизменяемый объект, можно использовать как ключ dict."""
    element: str
    ratio_13C_12C: float

    def __str__(self) -> str:
        return f"{self.element}: δ¹³C = {self.ratio_13C_12C:.4f}"


ir = IsotopeRatio("C", -25.3)
print(f"\n{ir}")

# frozen объекты hashable — можно в set и dict
ratios = {ir, IsotopeRatio("C", -27.1), IsotopeRatio("N", 3.5)}
lookup = {IsotopeRatio("C", -25.3): "Органика"}
print(f"Поиск: {lookup.get(ir, 'не найдено')}")

# Попытка изменить — ошибка:
try:
    ir.ratio_13C_12C = 0.0
except Exception as e:
    print(f"Нельзя изменить frozen: {type(e).__name__}")


# ───────────────────────────────────────────────────────────────
# asdict и astuple — сериализация dataclass
# ───────────────────────────────────────────────────────────────

p = Peak(5.2, 1200.0, "Кофеин", True)
print(f"\nasdict: {asdict(p)}")
print(f"astuple: {astuple(p)}")


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 1: dataclass NewsItem с сортировкой
# ───────────────────────────────────────────────────────────────
# Создай dataclass NewsItem (финансовая новость):
#   headline: str       — заголовок
#   source: str         — источник ("reuters", "bloomberg", "ft", ...)
#   category: str       — категория ("macro", "equity", "commodity", "crypto")
#   published_at: datetime  — дата и время публикации
#   reliability: float = 0.5  — оценка достоверности 0.0–1.0
#
# Требования:
#   - order=True (сортировка по умолчанию по reliability DESC)
#     Подсказка: sort_index: float = field(init=False, repr=False)
#     задай в __post_init__ как -reliability (тогда sorted() даст убывание)
#   - __post_init__: reliability должен быть 0.0–1.0, иначе ValueError
#   - метод age_hours() -> float — сколько часов с момента публикации (от now())
#
# Создай список из 5 новостей, отсортируй по reliability (убывание),
# выведи только новости из "reuters" или "bloomberg".

# >>> ПИШИ ЗДЕСЬ <<<


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 2: dataclass APIConfig с валидацией
# ───────────────────────────────────────────────────────────────
# Создай dataclass APIConfig:
#   api_url: str         — должен начинаться с "https://"
#   timeout: float       — секунды, диапазон 1.0 – 300.0
#   retries: int         — от 1 до 10
#   api_key: str = ""    — необязательный, repr=False (скрыть из repr!)
#   _validated: bool = field(init=False, repr=False)  — True если прошло
#
# В __post_init__ проверить все поля, установить _validated = True
#
# Пример:
#   cfg = APIConfig("https://api.alphavantage.co", 30.0, 3)
#   print(cfg)  # api_key не виден!

# >>> ПИШИ ЗДЕСЬ <<<


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 3 (сравнение): dataclass OHLCV + вручную
# ───────────────────────────────────────────────────────────────
# Сначала напиши dataclass OHLCV (ценовая свеча):
#   ticker: str, timestamp: datetime
#   open: float, high: float, low: float, close: float, volume: float
#   with order=True (сортировка по timestamp)
#
# Затем напиши класс OHLCVManual — ТО ЖЕ ЧТО OHLCV, но БЕЗ @dataclass:
# — напиши __init__, __repr__, __eq__, __lt__ вручную.
# Это наглядно показывает сколько бойлерплейта экономит @dataclass.

# >>> ПИШИ ЗДЕСЬ <<<

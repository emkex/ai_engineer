# ═══════════════════════════════════════════════════════════════
# ТЕМА 4: Полиморфизм и Duck Typing
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   Полиморфизм — один интерфейс, разные реализации.
#   Один и тот же метод ведёт себя по-разному в разных классах.
#
#   В Python полиморфизм реализуется через:
#   1. Переопределение методов (override) в подклассах
#   2. Duck Typing — "если объект крякает как утка, это утка"
#      Функция не проверяет тип — просто вызывает метод.
#      Если метод есть — работает. Если нет — TypeError.
#
#   Duck Typing позволяет писать обобщённый код без явного наследования.
#
# ───────────────────────────────────────────────────────────────
# ПРИМЕР: Детекторы (переопределение методов)
# ───────────────────────────────────────────────────────────────


class Detector:
    """Базовый класс детектора."""

    def detect(self, sample: dict) -> float:
        raise NotImplementedError

    def name(self) -> str:
        return self.__class__.__name__


class UVDetector(Detector):
    """УФ-детектор: измеряет поглощение при заданной длине волны."""

    def __init__(self, wavelength_nm: int = 254) -> None:
        self.wavelength_nm = wavelength_nm

    def detect(self, sample: dict) -> float:
        # имитация: поглощение зависит от концентрации
        return round(sample.get("concentration", 0) * 0.85, 3)

    def name(self) -> str:
        return f"УФ-детектор ({self.wavelength_nm} нм)"


class FluorescenceDetector(Detector):
    """Флуоресцентный детектор: более чувствительный."""

    def detect(self, sample: dict) -> float:
        return round(sample.get("concentration", 0) * 2.3, 3)

    def name(self) -> str:
        return "Флуоресцентный детектор"


class MassSpectrometer(Detector):
    """Масс-спектрометр: даёт молярные массы."""

    def detect(self, sample: dict) -> float:
        return round(sample.get("molar_mass", 0), 1)

    def name(self) -> str:
        return "Масс-спектрометр"


def run_analysis(detector: Detector, samples: list[dict]) -> list[float]:
    """Полиморфный запуск — работает с любым детектором."""
    print(f"\nАнализ с: {detector.name()}")
    results = []
    for s in samples:
        result = detector.detect(s)
        results.append(result)
        print(f"  Образец '{s.get('id', '?')}': {result}")
    return results


# Демонстрация
samples = [
    {"id": "A1", "concentration": 12.5, "molar_mass": 194.19},
    {"id": "A2", "concentration": 7.3, "molar_mass": 180.16},
    {"id": "A3", "concentration": 25.0, "molar_mass": 342.30},
]

detectors = [UVDetector(280), FluorescenceDetector(), MassSpectrometer()]
for d in detectors:
    run_analysis(d, samples)


# ───────────────────────────────────────────────────────────────
# ПРИМЕР: Duck Typing
# ───────────────────────────────────────────────────────────────

class FileReader:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def read(self) -> list[dict]:
        # имитация чтения файла
        print(f"Читаю файл: {self.filepath}")
        return [{"source": "file", "value": 42}]


class DatabaseReader:
    def __init__(self, query: str) -> None:
        self.query = query

    def read(self) -> list[dict]:
        # имитация запроса к БД
        print(f"Выполняю запрос: {self.query}")
        return [{"source": "db", "value": 99}]


class APIReader:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    def read(self) -> list[dict]:
        # имитация API запроса
        print(f"Запрос к API: {self.endpoint}")
        return [{"source": "api", "value": 7}]


def process_data(reader) -> None:
    """Duck typing: не проверяем тип, просто вызываем .read()"""
    data = reader.read()
    print(f"  Получено записей: {len(data)}")
    for record in data:
        print(f"  → {record}")


print("\n─── Duck Typing ───")
readers = [
    FileReader("data/results.csv"),
    DatabaseReader("SELECT * FROM samples"),
    APIReader("/api/v1/measurements"),
]
for reader in readers:
    process_data(reader)
    print()


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 1: Источники торговых сигналов
# ───────────────────────────────────────────────────────────────
# Создай базовый класс SignalSource с методами:
#   - generate(ticker: str) -> dict   — сигнал (NotImplementedError)
#     Возвращает: {"ticker": ..., "direction": "buy"/"sell"/"hold",
#                  "confidence": float 0–1, "source": ...}
#   - source_name() -> str  — название источника (NotImplementedError)
#   - describe(ticker: str) -> str
#     — "TechnicalAnalysis: BUY AAPL confidence=0.75"
#
# Подклассы (имитируй логику через random):
#   TechnicalAnalysis(lookback_days: int)
#   FundamentalAnalysis(universe: list[str])  — список тикеров в охвате
#   SentimentAnalysis()
#
# Напиши функции:
#   aggregate_signals(sources: list, ticker: str) -> dict
#     — итоговый сигнал: direction с наибольшим суммарным весом confidence
#   strongest_signal(sources: list, ticker: str) -> SignalSource
#     — источник с наивысшей confidence
#
# Покажи полиморфный запуск: for source in sources: source.describe(ticker)

# >>> ПИШИ ЗДЕСЬ <<<


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 2: Источники данных (Duck Typing)
# ───────────────────────────────────────────────────────────────
# Создай три класса БЕЗ общего родителя:
#   NewsAPIFetcher(api_url: str)   — метод fetch(query: str) -> list[dict]
#   ArchiveFetcher(archive_path: str) — метод fetch(query: str) -> list[dict]
#   DatabaseFetcher(table: str)    — метод fetch(query: str) -> list[dict]
#
# Каждый возвращает имитацию данных: список словарей
#   {"source": ..., "headline": ..., "timestamp": ...}
#
# Напиши функцию collect_data(fetcher, query: str) -> None
# которая вызывает fetcher.fetch(query) — без проверки типа (duck typing).
#
# Покажи что функция работает со всеми тремя классами.

# >>> ПИШИ ЗДЕСЬ <<<

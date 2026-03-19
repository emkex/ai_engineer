# ═══════════════════════════════════════════════════════════════
# ФИНАЛЬНЫЙ ПРОЕКТ: Система управления лабораторными анализами
# ═══════════════════════════════════════════════════════════════
#
# ЗАДАНИЕ (прочитай перед стартом):
#   Изучи этот файл как готовый пример архитектуры.
#   Когда разберёшься — реши задачу внизу файла (ищи # >>> ЗАДАЧА <<<).
#
# Применяет ВСЕ темы недели:
#   ✓ Классы, __init__, self, методы
#   ✓ Инкапсуляция, @property
#   ✓ Наследование, super()
#   ✓ Полиморфизм, duck typing
#   ✓ Dunder методы (__len__, __iter__, __add__, __repr__)
#   ✓ @dataclass для структур данных
#   ✓ ABC — контракт для методов анализа
#   ✓ SOLID — SRP, OCP, DIP
#
# СЦЕНАРИЙ:
#   Лаборатория получает образцы → выбирает метод анализа →
#   запускает анализ → собирает результаты → генерирует отчёт.
#   Метод анализа можно поменять без изменения кода лаборатории.
#
# ═══════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import random


# ───────────────────────────────────────────────────────────────
# Структуры данных (dataclass)
# ───────────────────────────────────────────────────────────────

@dataclass
class Sample:
    """Образец для анализа."""
    sample_id: str
    matrix: str              # тип матрицы: "вода", "почва", "пища"
    concentration: float     # предполагаемая концентрация мкг/л
    priority: int = 1        # приоритет 1-5

    def __post_init__(self) -> None:
        if not 1 <= self.priority <= 5:
            raise ValueError(f"Приоритет должен быть 1-5, получено: {self.priority}")


@dataclass
class AnalysisResult:
    """Результат одного анализа."""
    sample_id: str
    method_name: str
    measurements: dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    passed_qc: bool = True
    notes: str = ""

    def __repr__(self) -> str:
        status = "✓" if self.passed_qc else "✗"
        return f"AnalysisResult[{status}] {self.sample_id} ({self.method_name})"


# ───────────────────────────────────────────────────────────────
# ABC: Контракт для методов анализа (DIP)
# ───────────────────────────────────────────────────────────────

class AnalysisMethod(ABC):
    """
    Абстрактный базовый класс метода анализа.
    Лаборатория зависит от этой абстракции, не от конкретных методов.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Название метода."""
        ...

    @abstractmethod
    def prepare(self, sample: Sample) -> dict:
        """Подготовка образца."""
        ...

    @abstractmethod
    def measure(self, prepared: dict) -> dict[str, float]:
        """Проведение измерений. Возвращает словарь имя→значение."""
        ...

    @abstractmethod
    def qc_check(self, measurements: dict[str, float]) -> tuple[bool, str]:
        """Контроль качества. Возвращает (passed, notes)."""
        ...

    def run(self, sample: Sample) -> AnalysisResult:
        """Шаблонный метод: полный цикл анализа."""
        print(f"  [{self.name}] Подготовка '{sample.sample_id}'...")
        prepared = self.prepare(sample)
        measurements = self.measure(prepared)
        passed, notes = self.qc_check(measurements)
        return AnalysisResult(
            sample_id=sample.sample_id,
            method_name=self.name,
            measurements=measurements,
            passed_qc=passed,
            notes=notes,
        )


# ───────────────────────────────────────────────────────────────
# Конкретные методы анализа
# ───────────────────────────────────────────────────────────────

class HPLCAnalysis(AnalysisMethod):
    """ВЭЖХ — высокоэффективная жидкостная хроматография."""

    def __init__(self, column: str = "C18", wavelength_nm: int = 254) -> None:
        self._column = column
        self._wavelength = wavelength_nm

    @property
    def name(self) -> str:
        return f"ВЭЖХ/{self._column}/{self._wavelength}нм"

    def prepare(self, sample: Sample) -> dict:
        return {
            "sample": sample,
            "diluted": sample.concentration > 100,  # разбавляем концентрированные
            "volume_ul": 10,
        }

    def measure(self, prepared: dict) -> dict[str, float]:
        sample: Sample = prepared["sample"]
        base = sample.concentration
        if prepared["diluted"]:
            base /= 10
        return {
            "peak_main": round(base * random.uniform(0.9, 1.1), 3),
            "peak_impurity": round(base * random.uniform(0.01, 0.05), 3),
            "retention_time_min": round(random.uniform(4.5, 5.5), 2),
        }

    def qc_check(self, measurements: dict[str, float]) -> tuple[bool, str]:
        rt = measurements.get("retention_time_min", 0)
        passed = 4.0 <= rt <= 6.0
        note = "" if passed else f"Время удерживания вне диапазона: {rt:.2f} мин"
        return passed, note


class ICPMSAnalysis(AnalysisMethod):
    """ИСП-МС — определение элементного состава."""

    LIMITS = {"Pb": 10.0, "Cd": 5.0, "As": 10.0, "Hg": 1.0}  # ПДК мкг/л

    @property
    def name(self) -> str:
        return "ИСП-МС"

    def prepare(self, sample: Sample) -> dict:
        return {"sample": sample, "acid_digested": True, "dilution_factor": 5}

    def measure(self, prepared: dict) -> dict[str, float]:
        sample: Sample = prepared["sample"]
        df = prepared["dilution_factor"]
        base = sample.concentration / df
        return {
            element: round(base * random.uniform(0.05, 1.5), 4)
            for element in self.LIMITS
        }

    def qc_check(self, measurements: dict[str, float]) -> tuple[bool, str]:
        violations = [
            f"{el}={v:.3f} (ПДК={self.LIMITS[el]})"
            for el, v in measurements.items()
            if v > self.LIMITS.get(el, float("inf"))
        ]
        passed = len(violations) == 0
        notes = "Превышены ПДК: " + ", ".join(violations) if violations else ""
        return passed, notes


# ───────────────────────────────────────────────────────────────
# Контейнер результатов (dunder методы)
# ───────────────────────────────────────────────────────────────

class ResultCollection:
    """Коллекция результатов анализа с удобным интерфейсом."""

    def __init__(self) -> None:
        self._results: list[AnalysisResult] = []

    def add(self, result: AnalysisResult) -> None:
        self._results.append(result)

    def __len__(self) -> int:
        return len(self._results)

    def __getitem__(self, index: int) -> AnalysisResult:
        return self._results[index]

    def __iter__(self):
        return iter(self._results)

    def __contains__(self, sample_id: str) -> bool:
        return any(r.sample_id == sample_id for r in self._results)

    def __add__(self, other: "ResultCollection") -> "ResultCollection":
        """Объединение двух коллекций."""
        merged = ResultCollection()
        merged._results = self._results + other._results
        return merged

    def __repr__(self) -> str:
        passed = sum(1 for r in self._results if r.passed_qc)
        return (f"ResultCollection: {len(self)} результатов, "
                f"{passed} прошли QC, {len(self) - passed} с замечаниями")

    def passed(self) -> list[AnalysisResult]:
        """Только прошедшие контроль качества."""
        return [r for r in self._results if r.passed_qc]

    def failed(self) -> list[AnalysisResult]:
        """Только не прошедшие QC."""
        return [r for r in self._results if not r.passed_qc]


# ───────────────────────────────────────────────────────────────
# Лаборатория (оркестратор — DIP + SRP)
# ───────────────────────────────────────────────────────────────

class Laboratory:
    """
    Управляет процессом анализа.
    Зависит от абстракции AnalysisMethod (DIP).
    Не знает о конкретных реализациях методов.
    """

    def __init__(self, name: str, method: AnalysisMethod) -> None:
        self.name = name
        self._method = method
        self._results = ResultCollection()

    @property
    def method(self) -> AnalysisMethod:
        return self._method

    @method.setter
    def method(self, new_method: AnalysisMethod) -> None:
        """Смена метода анализа без изменения остального кода."""
        print(f"[{self.name}] Смена метода: {self._method.name} → {new_method.name}")
        self._method = new_method

    def process_sample(self, sample: Sample) -> AnalysisResult:
        """Обработка одного образца."""
        result = self._method.run(sample)
        self._results.add(result)
        return result

    def process_batch(self, samples: list[Sample]) -> ResultCollection:
        """Пакетная обработка — по приоритету."""
        sorted_samples = sorted(samples, key=lambda s: s.priority, reverse=True)
        batch = ResultCollection()
        print(f"\n[{self.name}] Запуск пакета: {len(samples)} образцов, метод: {self._method.name}")
        for sample in sorted_samples:
            result = self._method.run(sample)
            self._results.add(result)
            batch.add(result)
        return batch

    def summary_report(self) -> str:
        """Сводный отчёт по всем результатам."""
        lines = [
            f"{'═'*50}",
            f" Лаборатория: {self.name}",
            f" Метод: {self._method.name}",
            f" Всего образцов: {len(self._results)}",
            f" Прошли QC: {len(self._results.passed())}",
            f" С замечаниями: {len(self._results.failed())}",
            f"{'─'*50}",
        ]
        for r in self._results.failed():
            lines.append(f" ✗ {r.sample_id}: {r.notes}")
        lines.append(f"{'═'*50}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# ДЕМО: запуск системы
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Создаём образцы
    samples = [
        Sample("W-001", "вода", 12.5, priority=3),
        Sample("W-002", "вода", 250.0, priority=5),  # высокий приоритет
        Sample("S-001", "почва", 85.0, priority=2),
        Sample("F-001", "пища", 5.3, priority=4),
        Sample("W-003", "вода", 0.8, priority=1),
    ]

    # Лаборатория с ВЭЖХ
    lab = Laboratory("Аналитическая лаборатория №1", HPLCAnalysis("C18", 280))

    # Пакетная обработка
    batch1 = lab.process_batch(samples[:3])
    print(f"\nПакет 1: {batch1}")

    # Смена метода — код лаборатории НЕ МЕНЯЕТСЯ (OCP + DIP)
    lab.method = ICPMSAnalysis()
    batch2 = lab.process_batch(samples[3:])
    print(f"\nПакет 2: {batch2}")

    # Объединение коллекций через __add__
    all_results = batch1 + batch2
    print(f"\nВсе результаты: {all_results}")

    # Отчёт
    print(lab.summary_report())

    # Итерация по результатам (через __iter__)
    print("\nПрошедшие QC:")
    for result in lab._results.passed():
        print(f"  {result}")

    # Проверка наличия образца (__contains__)
    print(f"\n'W-001' в результатах: {'W-001' in lab._results}")
    print(f"'X-999' в результатах: {'X-999' in lab._results}")


# ═══════════════════════════════════════════════════════════════
# >>> ЗАДАЧА <<<: Перепиши проект для финансового домена
# ═══════════════════════════════════════════════════════════════
#
# Используя ту же архитектуру (ABC + dataclass + dunder + SOLID),
# построй систему обработки торговых сигналов:
#
# Структуры данных (dataclass):
#   MarketData  — данные по инструменту: ticker, price, volume, timestamp
#   SignalResult — результат генерации сигнала: ticker, direction, confidence,
#                  source_name, timestamp, passed_filter: bool, notes: str
#
# ABC SignalStrategy (аналог AnalysisMethod):
#   @property @abstractmethod name() -> str
#   @abstractmethod prepare(data: MarketData) -> dict
#   @abstractmethod generate(prepared: dict) -> dict[str, float]
#   @abstractmethod filter_check(result: dict) -> tuple[bool, str]
#   Шаблонный метод run(data: MarketData) -> SignalResult
#
# Конкретные стратегии (2–3 штуки, имитируй логику через random):
#   MomentumStrategy(lookback: int)
#   MeanReversionStrategy(threshold: float)
#
# Контейнер SignalCollection (аналог ResultCollection):
#   — поддержка __len__, __iter__, __getitem__, __contains__, __add__
#   — методы: passed() / failed(), summary_repr()
#
# Оркестратор SignalEngine (аналог Laboratory):
#   — принимает стратегию через DIP
#   — метод process_ticker(data: MarketData) -> SignalResult
#   — метод process_watchlist(watchlist: list[MarketData]) -> SignalCollection
#   — метод смены стратегии без изменения остального кода (OCP)
#
# >>> ПИШИ ЗДЕСЬ <<<

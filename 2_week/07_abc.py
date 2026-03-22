# ═══════════════════════════════════════════════════════════════
# ТЕМА 7: ABC — Абстрактные базовые классы
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   ABC (Abstract Base Class) — класс, который нельзя инстанцировать напрямую.
#   Он задаёт КОНТРАКТ: подкласс ОБЯЗАН реализовать все @abstractmethod.
#   Если подкласс не реализует хотя бы один — TypeError при создании объекта.
#
#   from abc import ABC, abstractmethod
#
#   class MyABC(ABC):
#       @abstractmethod
#       def my_method(self) -> str: ...    # обязателен в подклассах
#
#       def concrete_method(self): ...     # обычный метод — уже реализован
#
#   Зачем ABC:
#   - Явный контракт — документирует что ДОЛЖЕН делать подкласс
#   - Ошибка на этапе создания объекта, а не при вызове метода
#   - Лучше duck typing когда важна явная иерархия и типизация
#
#   @abstractmethod + @property — абстрактное свойство
#   @abstractmethod + @classmethod — абстрактный метод класса
#
#   Шаблонный метод (Template Method) — конкретный метод в ABC
#   который вызывает abstractmethod — определяет алгоритм в базовом классе.
#
# ───────────────────────────────────────────────────────────────
# ПРИМЕР 1: Методы аналитического анализа
# ───────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AnalysisResult:
    """Результат анализа."""
    sample_id: str
    method_name: str
    values: dict
    timestamp: datetime = field(default_factory=datetime.now)
    passed: bool = True


class AnalysisMethod(ABC):
    """Абстрактный базовый класс для методов аналитического анализа."""

    @abstractmethod
    def prepare_sample(self, sample: dict) -> dict:
        """Подготовка образца к анализу."""
        ...

    @abstractmethod
    def run(self, prepared_sample: dict) -> dict:
        """Проведение анализа."""
        ...

    @abstractmethod
    def validate(self, results: dict) -> bool:
        """Проверка корректности результатов."""
        ...

    @property
    @abstractmethod
    def method_name(self) -> str:
        """Название метода."""
        ...

    def full_pipeline(self, sample: dict) -> AnalysisResult:
        """
        Шаблонный метод — определяет алгоритм,
        конкретные шаги реализуются в подклассах.
        """
        print(f"[{self.method_name}] Начало анализа образца '{sample.get('id')}'")
        prepared = self.prepare_sample(sample)
        results = self.run(prepared)
        passed = self.validate(results)
        return AnalysisResult(
            sample_id=sample.get("id", "unknown"),
            method_name=self.method_name,
            values=results,
            passed=passed
        )


class HPLCMethod(AnalysisMethod):
    """ВЭЖХ метод анализа."""

    def __init__(self, column: str, flow_rate: float) -> None:
        self.column = column
        self.flow_rate = flow_rate

    @property
    def method_name(self) -> str:
        return f"ВЭЖХ ({self.column})"

    def prepare_sample(self, sample: dict) -> dict:
        print(f"  Фильтрация и разбавление образца 1:10")
        return {**sample, "dilution": 10, "filtered": True}

    def run(self, prepared: dict) -> dict:
        import random
        return {
            "peak_1": round(random.uniform(10, 100), 2),
            "peak_2": round(random.uniform(5, 50), 2),
            "retention_time": round(random.uniform(2, 15), 2),
        }

    def validate(self, results: dict) -> bool:
        return results.get("peak_1", 0) > 0 and results.get("peak_2", 0) > 0


class IcpMsMethod(AnalysisMethod):
    """ИСП-МС метод (масс-спектрометрия с индуктивно связанной плазмой)."""

    @property
    def method_name(self) -> str:
        return "ИСП-МС"

    def prepare_sample(self, sample: dict) -> dict:
        print(f"  Кислотное разложение образца")
        return {**sample, "acid_digested": True, "matrix": "HNO3 2%"}

    def run(self, prepared: dict) -> dict:
        import random
        elements = ["Pb", "Cd", "As", "Hg", "Cu"]
        return {el: round(random.uniform(0.001, 10.0), 4) for el in elements}

    def validate(self, results: dict) -> bool:
        # проверяем что свинец не превышает норму (10 мкг/л)
        return results.get("Pb", 0) <= 10.0


# Демонстрация
print("─── ABC: Методы анализа ───")

# Нельзя создать экземпляр абстрактного класса:
try:
    method = AnalysisMethod()
except TypeError as e:
    print(f"Нельзя создать экземпляр ABC: {e}\n")

sample = {"id": "S-001", "matrix": "вода", "concentration": 5.0}

hplc = HPLCMethod("C18 250мм", flow_rate=1.0)
result = hplc.full_pipeline(sample)
print(f"Результат: {result}\n")

icp = IcpMsMethod()
result2 = icp.full_pipeline(sample)
print(f"Результат: {result2}")


# ───────────────────────────────────────────────────────────────
# ПРИМЕР 2: Класс без реализации всех методов → ошибка
# ───────────────────────────────────────────────────────────────

class IncompleteMethod(AnalysisMethod):
    """Этот класс не реализует все abstractmethod."""

    @property
    def method_name(self) -> str:
        return "Неполный"

    def prepare_sample(self, sample: dict) -> dict:
        return sample

    # run() и validate() НЕ реализованы!


try:
    bad = IncompleteMethod()
except TypeError as e:
    print(f"\nОшибка неполной реализации ABC:\n  {e}")


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 1: ABC CapitalSource (источник ликвидности)
# ───────────────────────────────────────────────────────────────
# Создай ABC CapitalSource:
#   @abstractmethod get_capital_usd() -> float   — объём капитала в USD (для сравнения)
#   @abstractmethod flow_direction() -> str      — "inflow" / "outflow" / "neutral"
#   @property @abstractmethod source_name() -> str
#
#   Конкретный метод describe() -> str — выводит в читаемых единицах:
#     "Federal Reserve: $8.50T | inflow"
#     "Citadel: $62.00B | outflow"
#     (триллионы для ЦБ, миллиарды для остальных)
#
# Подклассы (имитируй данные):
#   CentralBank(name: str, reserve_trillions: float)
#     — крупнейший источник; flow_direction: > 7T → "inflow", иначе "outflow"
#   HedgeFund(name: str, aum_billions: float, strategy: str)
#     — подвижный игрок; flow_direction: "outflow" если strategy == "short", иначе "inflow"
#   CommercialBank(name: str, assets_billions: float)
#     — средний игрок; flow_direction всегда "neutral"
#
# Функции:
#   dominant_source(sources: list[CapitalSource]) -> CapitalSource
#     — источник с максимальным get_capital_usd()
#   net_flow(sources: list[CapitalSource]) -> str
#     — "net inflow" если inflow > outflow, "net outflow" если outflow > inflow,
#       "balanced" если поровну
#
# Проверь: попытка создать CapitalSource() → TypeError


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


class CapitalSource(ABC):
    """Абстрактный класс источника ликвидности."""

    @abstractmethod
    def get_capital_usd(self) -> float:
        """Объём капитала в USD (для сравнения источников)."""
        ...

    @abstractmethod
    def flow_direction(self) -> str:
        """Направление потока: 'inflow', 'outflow' или 'neutral'."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Название источника."""
        ...

    def describe(self) -> str:
        """Шаблонный метод — описание источника в читаемых единицах."""
        capital = self.get_capital_usd()
        direction = self.flow_direction()
        if capital >= 1e12:
            capital_str = f"${capital / 1e12:.2f}T"
        else:
            capital_str = f"${capital / 1e9:.2f}B"
        return f"{self.source_name}: {capital_str} | {direction}"


class CentralBank(CapitalSource):
    """Центральный банк — крупнейший источник ликвидности."""

    def __init__(self, name: str, reserve_trillions: float) -> None:
        self.name = name
        self.reserve_trillions = reserve_trillions

    @property
    def source_name(self) -> str:
        return self.name

    def get_capital_usd(self) -> float:
        """Резервы в триллионах → USD."""
        return self.reserve_trillions * 1e12

    def flow_direction(self) -> str:
        """Крупные резервы (>7T) — накачка ликвидности (inflow)."""
        return "inflow" if self.reserve_trillions > 7.0 else "outflow"


class HedgeFund(CapitalSource):
    """Хедж-фонд — подвижный игрок, направление зависит от стратегии."""

    def __init__(self, name: str, aum_billions: float, strategy: str) -> None:
        self.name = name
        self.aum_billions = aum_billions
        self.strategy = strategy  # "long" или "short"

    @property
    def source_name(self) -> str:
        return self.name

    def get_capital_usd(self) -> float:
        """AUM в миллиардах → USD."""
        return self.aum_billions * 1e9

    def flow_direction(self) -> str:
        """Short-стратегия давит на рынок (outflow), long — добавляет (inflow)."""
        return "outflow" if self.strategy == "short" else "inflow"


class CommercialBank(CapitalSource):
    """Коммерческий банк — средний игрок с нейтральным потоком."""

    def __init__(self, name: str, assets_billions: float) -> None:
        self.name = name
        self.assets_billions = assets_billions

    @property
    def source_name(self) -> str:
        return self.name

    def get_capital_usd(self) -> float:
        """Активы в миллиардах → USD."""
        return self.assets_billions * 1e9

    def flow_direction(self) -> str:
        """Коммерческие банки не создают направленного давления."""
        return "neutral"


def dominant_source(sources: list[CapitalSource]) -> CapitalSource:
    """Источник с максимальным капиталом."""
    return max(sources, key=lambda s: s.get_capital_usd())


def net_flow(sources: list[CapitalSource]) -> str:
    """Суммарный поток капитала по всем источникам."""
    inflow_count = sum(1 for s in sources if s.flow_direction() == "inflow")
    outflow_count = sum(1 for s in sources if s.flow_direction() == "outflow")

    if inflow_count > outflow_count:
        return "net inflow"
    elif outflow_count > inflow_count:
        return "net outflow"
    else:
        return "balanced"


# ─── ДЕМОНСТРАЦИЯ РАБОТЫ ───
print("─── ABC: Источники ликвидности ───\n")

# Попытка создать экземпляр ABC → TypeError
try:
    source = CapitalSource()
except TypeError as e:
    print(f"Нельзя создать CapitalSource(): {e}\n")

# Создание источников
fed = CentralBank("Federal Reserve", 8.5)      # > 7T → inflow
boj = CentralBank("Bank of Japan", 3.2)        # < 7T → outflow
citadel = HedgeFund("Citadel", 62.0, "long")   # long → inflow
melvin = HedgeFund("Melvin Capital", 12.5, "short")  # short → outflow
jpmorgan = CommercialBank("JP Morgan", 3800.0)
ubs = CommercialBank("UBS", 1400.0)

sources = [fed, boj, citadel, melvin, jpmorgan, ubs]

print("Источники ликвидности:")
for source in sources:
    print(f"  {source.describe()}")

print(f"\nДоминирующий источник: {dominant_source(sources).source_name}")
print(f"Суммарный поток: {net_flow(sources)}")



# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 2: ABC Serializer
# ───────────────────────────────────────────────────────────────
# Создай ABC Serializer:
#   @abstractmethod to_bytes(data: dict) -> bytes
#   @abstractmethod from_bytes(raw: bytes) -> dict
#   @property @abstractmethod format_name() -> str
#
#   Конкретный метод roundtrip(data: dict) -> bool:
#     сериализует и десериализует, возвращает True если данные совпадают
#
# Реализуй:
#   JSONSerializer  — использует json.dumps/loads + encode/decode
#   PickleSerializer — использует pickle.dumps/loads
#
# Покажи что оба работают через одинаковый интерфейс.
# Напиши функцию backup(serializer: Serializer, data: dict) -> bytes
# которая работает с любым подклассом.

# >>> ПИШИ ЗДЕСЬ <<<

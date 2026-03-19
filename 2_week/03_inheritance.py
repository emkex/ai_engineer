# ═══════════════════════════════════════════════════════════════
# ТЕМА 3: Наследование
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   Наследование позволяет создать новый класс на основе существующего.
#   Дочерний класс получает все атрибуты и методы родителя.
#
#   class Child(Parent):              — одиночное наследование
#   class Child(Parent1, Parent2):    — множественное наследование
#
#   super().__init__(...)  — вызов конструктора родителя (обязательно!)
#   super().method(...)    — вызов метода родителя (при переопределении)
#
#   MRO (Method Resolution Order) — порядок поиска метода в иерархии.
#   Смотреть: ClassName.__mro__ или help(ClassName)
#
#   isinstance(obj, Class)   — True если obj является экземпляром Class
#   issubclass(Child, Parent) — True если Child наследует от Parent
#
# ───────────────────────────────────────────────────────────────
# ПРИМЕР: Иерархия приборов
# ───────────────────────────────────────────────────────────────


class Instrument:
    """Базовый класс: лабораторный прибор."""

    def __init__(self, model: str, manufacturer: str) -> None:
        self.model = model
        self.manufacturer = manufacturer
        self._is_calibrated = False

    def calibrate(self) -> None:
        """Калибровка прибора."""
        self._is_calibrated = True
        print(f"{self.model}: калибровка выполнена")

    def measure(self) -> float:
        """Провести измерение. Переопределяется в подклассах."""
        raise NotImplementedError("Подкласс должен реализовать measure()")

    def status(self) -> str:
        cal = "откалиброван" if self._is_calibrated else "не откалиброван"
        return f"{self.manufacturer} {self.model} [{cal}]"


class HPLC(Instrument):
    """Высокоэффективная жидкостная хроматография."""

    def __init__(self, model: str, manufacturer: str, column_count: int) -> None:
        super().__init__(model, manufacturer)    # инициализируем родителя
        self.column_count = column_count
        self._current_column = 0

    def measure(self) -> float:
        """Имитация хроматографического измерения."""
        import random
        if not self._is_calibrated:
            print("Предупреждение: прибор не откалиброван!")
        return round(random.uniform(10.0, 100.0), 2)

    def switch_column(self, column_idx: int) -> None:
        if 0 <= column_idx < self.column_count:
            self._current_column = column_idx
            print(f"Активна колонка #{column_idx + 1}")
        else:
            raise ValueError(f"Колонка {column_idx} не существует")

    def status(self) -> str:
        base = super().status()   # берём статус родителя и расширяем
        return f"{base}, колонок: {self.column_count}"


class GasChromatograph(Instrument):
    """Газовый хроматограф."""

    def __init__(self, model: str, manufacturer: str, carrier_gas: str) -> None:
        super().__init__(model, manufacturer)
        self.carrier_gas = carrier_gas

    def measure(self) -> float:
        import random
        return round(random.uniform(0.1, 50.0), 3)

    def purge(self) -> None:
        print(f"Продувка {self.carrier_gas}...")


# Демонстрация
hplc = HPLC("Prominence", "Shimadzu", column_count=3)
gc = GasChromatograph("GC-2010", "Shimadzu", "He")

hplc.calibrate()
print(hplc.status())
print(f"Измерение: {hplc.measure()} mAU")
hplc.switch_column(1)

print()
print(f"isinstance(hplc, Instrument): {isinstance(hplc, Instrument)}")
print(f"isinstance(hplc, HPLC): {isinstance(hplc, HPLC)}")
print(f"isinstance(hplc, GasChromatograph): {isinstance(hplc, GasChromatograph)}")
print(f"issubclass(HPLC, Instrument): {issubclass(HPLC, Instrument)}")

# MRO — порядок разрешения методов
print(f"\nMRO HPLC: {[c.__name__ for c in HPLC.__mro__]}")


# ───────────────────────────────────────────────────────────────
# ПРИМЕР: Множественное наследование + Миксины
# ───────────────────────────────────────────────────────────────

class Serializable:
    """Миксин: умеет сериализоваться в словарь."""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


class Loggable:
    """Миксин: логирует действия."""

    def log(self, action: str) -> None:
        print(f"[LOG] {self.__class__.__name__}: {action}")


class SensorReading(Serializable, Loggable):
    """Показание датчика — использует оба миксина."""

    def __init__(self, sensor_id: str, value: float, unit: str) -> None:
        self.sensor_id = sensor_id
        self.value = value
        self.unit = unit

    def record(self) -> None:
        self.log(f"записано значение {self.value} {self.unit}")


reading = SensorReading("T-01", 23.5, "°C")
reading.record()
print(reading.to_dict())
print(f"MRO SensorReading: {[c.__name__ for c in SensorReading.__mro__]}")


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 1: Иерархия финансовых инструментов
# ───────────────────────────────────────────────────────────────
# Создай иерархию: FinancialInstrument → Equity → ETF
#
# FinancialInstrument:
#   - ticker: str, name: str, currency: str = "USD"
#   - describe() -> str  — "AAPL | Apple Inc. | USD"
#   - annual_return(years: int) -> float  — NotImplementedError
#
# Equity(FinancialInstrument):
#   - sector: str         — "Technology", "Energy", "Finance", ...
#   - market_cap: float   — капитализация в млрд USD
#   - annual_return(years) -> float  — market_cap * 0.08 / years  (упрощение)
#   - describe() -> str  — расширяет родительский (через super()), добавляет сектор
#
# ETF(Equity):
#   - holdings_count: int  — кол-во бумаг в фонде
#   - expense_ratio: float — TER в % (например 0.07)
#   - annual_return(years) -> float  — market_cap * 0.06 / years  (ETF дешевле)
#   - describe() -> str  — добавляет expense_ratio и holdings_count
#
# Напиши функцию compare_return(instruments: list, years: int)
# которая выводит все инструменты + их annual_return за years лет.
# Функция должна работать для любого подкласса FinancialInstrument.

# >>> ПИШИ ЗДЕСЬ <<<


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 2: Миксин Timestamped + NewsEvent
# ───────────────────────────────────────────────────────────────
# Создай миксин Timestamped:
#   - при создании объекта записывает datetime.now() в self.created_at
#   - метод age_seconds() -> float — сколько секунд прошло с создания
#
# Создай класс NewsEvent(Timestamped):
#   - headline: str       — заголовок новости
#   - source: str         — источник ("reuters", "bloomberg", "ft", ...)
#   - reliability: float  — оценка достоверности 0.0–1.0 (выставляется вручную)
#
# Покажи что при создании экземпляра created_at заполняется автоматически.
# Создай 4–5 новостей, отсортируй по reliability (убывание).

# >>> ПИШИ ЗДЕСЬ <<<

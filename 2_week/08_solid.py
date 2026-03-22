# ═══════════════════════════════════════════════════════════════
# ТЕМА 8: SOLID принципы
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   SOLID — 5 принципов проектирования ОО-кода (Robert C. Martin):
#
#   S — Single Responsibility Principle (SRP)
#       Класс должен иметь только одну причину для изменения.
#
#   O — Open/Closed Principle (OCP)
#       Открыт для расширения, закрыт для изменения.
#       Новый функционал — новый класс, а не правка старого.
#
#   L — Liskov Substitution Principle (LSP)
#       Подкласс должен быть полностью заменяем на базовый класс.
#       Если метод родителя гарантирует что-то — подкласс не должен нарушать это.
#
#   I — Interface Segregation Principle (ISP)
#       Много маленьких интерфейсов лучше одного большого.
#       Клиент не должен зависеть от методов, которые он не использует.
#
#   D — Dependency Inversion Principle (DIP)
#       Зависеть от абстракций, не от конкретных реализаций.
#       Высокоуровневые модули не должны зависеть от низкоуровневых.
#
# ═══════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod


# ───────────────────────────────────────────────────────────────
# S: Single Responsibility Principle
# ───────────────────────────────────────────────────────────────
#
# ПЛОХО: один класс делает слишком много

class ReportManagerBAD:
    """Нарушает SRP: и генерирует, и сохраняет, и отправляет."""

    def generate(self, data: dict) -> str:
        return f"Отчёт: {data}"

    def save_to_file(self, report: str, path: str) -> None:
        print(f"Сохраняю в {path}: {report}")

    def send_by_email(self, report: str, email: str) -> None:
        print(f"Отправляю на {email}: {report}")


# ХОРОШО: каждый класс — одна ответственность

class ReportGenerator:
    """Только генерирует отчёты."""
    def generate(self, data: dict) -> str:
        return f"Отчёт по данным: {data}"


class ReportStorage:
    """Только сохраняет отчёты."""
    def save(self, report: str, path: str) -> None:
        print(f"[Storage] Сохранено в '{path}'")


class ReportSender:
    """Только отправляет отчёты."""
    def send(self, report: str, recipient: str) -> None:
        print(f"[Email] Отправлено → {recipient}")


# Демонстрация SRP
data = {"sample": "S-001", "result": 42.5}
generator = ReportGenerator()
storage = ReportStorage()
sender = ReportSender()

report = generator.generate(data)
storage.save(report, "/reports/s001.txt")
sender.send(report, "lab@example.com")


# ───────────────────────────────────────────────────────────────
# O: Open/Closed Principle
# ───────────────────────────────────────────────────────────────
#
# ПЛОХО: добавление нового формата требует изменения существующего кода

class ExporterBAD:
    def export(self, data: dict, format: str) -> str:
        if format == "csv":
            return ",".join(str(v) for v in data.values())
        elif format == "json":
            import json
            return json.dumps(data)
        # Добавление XML → нужно менять этот класс! Нарушение OCP.


# ХОРОШО: расширяем через новые классы, не меняем старые

class Exporter(ABC):
    @abstractmethod
    def export(self, data: dict) -> str: ...


class CSVExporter(Exporter):
    def export(self, data: dict) -> str:
        return ",".join(str(v) for v in data.values())


class JSONExporter(Exporter):
    def export(self, data: dict) -> str:
        import json
        return json.dumps(data, ensure_ascii=False)


class XMLExporter(Exporter):
    """Новый формат — новый класс. Старый код не трогаем."""
    def export(self, data: dict) -> str:
        items = "".join(f"<{k}>{v}</{k}>" for k, v in data.items())
        return f"<data>{items}</data>"


def export_report(exporter: Exporter, data: dict) -> None:
    """Эта функция не меняется при добавлении новых форматов."""
    print(exporter.export(data))


print("\n─── OCP ───")
sample_data = {"id": "S-001", "value": 42.5, "unit": "мкг/л"}
for exporter in [CSVExporter(), JSONExporter(), XMLExporter()]:
    export_report(exporter, sample_data)


# ───────────────────────────────────────────────────────────────
# L: Liskov Substitution Principle
# ───────────────────────────────────────────────────────────────
#
# Классический пример нарушения LSP: Rectangle → Square

class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self._width = width
        self._height = height

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, v: float) -> None:
        self._width = v

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, v: float) -> None:
        self._height = v

    def area(self) -> float:
        return self._width * self._height


class SquareBAD(Rectangle):
    """Нарушает LSP: меняет контракт Rectangle."""

    @Rectangle.width.setter
    def width(self, v: float) -> None:
        self._width = v
        self._height = v  # ← неожиданное поведение!

    @Rectangle.height.setter
    def height(self, v: float) -> None:
        self._width = v
        self._height = v  # ← нарушение ожиданий


def check_rectangle(r: Rectangle) -> None:
    """Функция ожидает: установка ширины не меняет высоту."""
    r.width = 5
    r.height = 10
    expected = 50
    actual = r.area()
    print(f"Ожидалось {expected}, получено {actual} — {'OK' if actual == expected else 'LSP НАРУШЕН'}")


print("\n─── LSP ───")
check_rectangle(Rectangle(1, 1))  # OK
check_rectangle(SquareBAD(1, 1))  # LSP НАРУШЕН!

# РЕШЕНИЕ: Square НЕ наследует от Rectangle — они несовместимы по поведению.
# Оба могут наследовать от Shape с методом area().


# ───────────────────────────────────────────────────────────────
# I: Interface Segregation Principle
# ───────────────────────────────────────────────────────────────
#
# ПЛОХО: один большой интерфейс заставляет реализовывать лишнее

class DeviceBAD(ABC):
    """Слишком большой интерфейс."""
    @abstractmethod
    def read(self) -> float: ...
    @abstractmethod
    def write(self, value: float) -> None: ...
    @abstractmethod
    def calibrate(self) -> None: ...
    @abstractmethod
    def stream(self): ...   # не всем устройствам нужен стриминг!


# ХОРОШО: маленькие интерфейсы по ответственности

class Readable(ABC):
    @abstractmethod
    def read(self) -> float: ...


class Writable(ABC):
    @abstractmethod
    def write(self, value: float) -> None: ...


class Calibratable(ABC):
    @abstractmethod
    def calibrate(self) -> None: ...


class ReadOnlySensor(Readable, Calibratable):
    """Датчик: только чтение и калибровка — не нужен write()."""

    def read(self) -> float:
        import random
        return round(random.uniform(20.0, 25.0), 2)

    def calibrate(self) -> None:
        print("Калибровка датчика...")


class FullDevice(Readable, Writable, Calibratable):
    """Полноценное устройство — реализует все интерфейсы."""

    def read(self) -> float:
        return 42.0

    def write(self, value: float) -> None:
        print(f"Запись: {value}")

    def calibrate(self) -> None:
        print("Калибровка устройства...")


print("\n─── ISP ───")
sensor = ReadOnlySensor()
print(f"Датчик: {sensor.read()}")
sensor.calibrate()


# ───────────────────────────────────────────────────────────────
# D: Dependency Inversion Principle
# ───────────────────────────────────────────────────────────────
#
# ПЛОХО: зависимость от конкретного класса

class MySQLDatabaseBAD:
    def save(self, data: dict) -> None:
        print(f"[MySQL] Сохраняем: {data}")


class AnalysisServiceBAD:
    def __init__(self) -> None:
        self.db = MySQLDatabaseBAD()  # ← жёсткая зависимость!

    def analyze_and_save(self, sample: dict) -> None:
        result = {"sample": sample, "result": 42.0}
        self.db.save(result)


# ХОРОШО: зависим от абстракции

class AbstractDatabase(ABC):
    @abstractmethod
    def save(self, data: dict) -> None: ...

    @abstractmethod
    def load(self, record_id: str) -> dict: ...


class MySQLDatabase(AbstractDatabase):
    def save(self, data: dict) -> None:
        print(f"[MySQL] Сохраняем: {data}")

    def load(self, record_id: str) -> dict:
        return {"id": record_id, "source": "MySQL"}


class InMemoryDatabase(AbstractDatabase):
    """Для тестирования — вся БД в памяти."""

    def __init__(self) -> None:
        self._store: dict = {}

    def save(self, data: dict) -> None:
        key = data.get("id", str(len(self._store)))
        self._store[key] = data
        print(f"[InMemory] Сохранено с ключом '{key}'")

    def load(self, record_id: str) -> dict:
        return self._store.get(record_id, {})


class AnalysisService:
    """Зависит от абстракции — можно подставить любую БД."""

    def __init__(self, db: AbstractDatabase) -> None:
        self.db = db

    def analyze_and_save(self, sample: dict) -> None:
        result = {**sample, "result": 42.0, "id": sample.get("id", "x")}
        self.db.save(result)


print("\n─── DIP ───")
# В проде — реальная БД
prod_service = AnalysisService(MySQLDatabase())
prod_service.analyze_and_save({"id": "S-001", "compound": "Pb"})

# В тестах — InMemory БД (без внешних зависимостей)
test_db = InMemoryDatabase()
test_service = AnalysisService(test_db)
test_service.analyze_and_save({"id": "T-001", "compound": "Cd"})
print(f"Из тестовой БД: {test_db.load('T-001')}")


# ═══════════════════════════════════════════════════════════════
# ЗАДАЧА: Рефакторинг "плохой" системы алертов
# ═══════════════════════════════════════════════════════════════
#
# Дана система торговых алертов с нарушениями всех 5 принципов SOLID.
# Проведи рефакторинг: применить SRP, OCP, LSP, ISP, DIP.

class AlertServiceBAD:
    """
    Нарушает ВСЕ принципы SOLID.
    S: делает слишком много (форматирование, доставка, логирование)
    O: добавление нового канала требует изменения класса
    I: один большой класс вместо маленьких интерфейсов
    D: жёстко зависит от конкретных реализаций
    """

    def __init__(self) -> None:
        self.log: list[str] = []

    def alert(self, signal: dict, channel: str, recipient: str) -> None:
        # форматируем
        ticker = signal.get("ticker", "?")
        direction = signal.get("direction", "hold").upper()
        confidence = signal.get("confidence", 0.0)
        formatted = f"[{direction}] {ticker} | confidence={confidence:.0%}"

        # доставляем
        if channel == "email":
            print(f"Email → {recipient}: {formatted}")
        elif channel == "telegram":
            print(f"Telegram → {recipient}: {formatted[:200]}")  # лимит
        elif channel == "sms":
            print(f"SMS → {recipient}: {formatted[:160]}")  # SMS лимит
        # ДОБАВИТЬ SLACK: нужно МЕНЯТЬ ЭТОТ КЛАСС (нарушение OCP)

        # логируем
        entry = f"{channel}: {recipient} — {formatted}"
        self.log.append(entry)
        print(f"[LOG] {entry}")

    def get_log(self) -> list[str]:
        return self.log


# Демонстрация "плохого" кода:
bad_service = AlertServiceBAD()
bad_service.alert({"ticker": "AAPL", "direction": "buy", "confidence": 0.82}, "email", "trader@fund.com")
bad_service.alert({"ticker": "BTC", "direction": "sell", "confidence": 0.65}, "telegram", "@fund_bot")


# ─── РЕШЕНИЕ ───────────────────────────────────────────────────

from abc import ABC, abstractmethod

# ISP: три отдельных абстракции вместо одного большого класса

class IFormatter(ABC):
    @abstractmethod
    def format(self, signal: dict) -> str: ...


class ISender(ABC):
    @abstractmethod
    def send(self, message: str, recipient: str) -> None: ...


class ILogger(ABC):
    @abstractmethod
    def log(self, entry: str) -> None: ...


# SRP: каждый класс — одна задача

class SignalFormatter(IFormatter):
    """Форматирует торговый сигнал в строку."""

    def format(self, signal: dict) -> str:
        ticker = signal.get("ticker", "?")
        direction = signal.get("direction", "hold").upper()
        confidence = signal.get("confidence", 0.0)
        return f"[{direction}] {ticker} | confidence={confidence:.0%}"


class InMemoryLogger(ILogger):
    """Хранит лог в памяти."""

    def __init__(self) -> None:
        self._entries: list[str] = []

    def log(self, entry: str) -> None:
        self._entries.append(entry)
        print(f"[LOG] {entry}")

    def get_entries(self) -> list[str]:
        return self._entries


# OCP + LSP: новые каналы — новые классы, старый код не трогаем

class EmailSender(ISender):
    def send(self, message: str, recipient: str) -> None:
        print(f"Email → {recipient}: {message}")


class TelegramSender(ISender):
    def send(self, message: str, recipient: str) -> None:
        print(f"Telegram → {recipient}: {message[:200]}")


class SmsSender(ISender):
    def send(self, message: str, recipient: str) -> None:
        print(f"SMS → {recipient}: {message[:160]}")


class SlackSender(ISender):
    """Новый канал — добавлен без изменения существующего кода (OCP)."""

    def send(self, message: str, recipient: str) -> None:
        print(f"Slack → #{recipient}: {message}")


# DIP: AlertService зависит только от абстракций

class AlertService:
    """
    Знает только об абстракциях IFormatter, ISender, ILogger.
    Конкретные реализации инжектируются снаружи.
    """

    def __init__(self, formatter: IFormatter, sender: ISender, logger: ILogger) -> None:
        self.formatter = formatter
        self.sender = sender
        self.logger = logger

    def alert(self, signal: dict, recipient: str) -> None:
        message = self.formatter.format(signal)
        self.sender.send(message, recipient)
        self.logger.log(f"{recipient} — {message}")


# Демонстрация:
print("\n─── SOLID AlertService ───")

logger = InMemoryLogger()
formatter = SignalFormatter()

# Разные каналы — один и тот же интерфейс (LSP)
signals = [
    ({"ticker": "AAPL", "direction": "buy", "confidence": 0.82}, EmailSender(), "trader@fund.com"),
    ({"ticker": "BTC", "direction": "sell", "confidence": 0.65}, TelegramSender(), "@fund_bot"),
    ({"ticker": "NVDA", "direction": "buy", "confidence": 0.91}, SlackSender(), "alerts"),
]

for signal, sender, recipient in signals:
    AlertService(formatter, sender, logger).alert(signal, recipient)

print(f"\nВсего алертов в логе: {len(logger.get_entries())}")

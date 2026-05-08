"""
ФАЙЛ 1: Pydantic без AI — корни библиотеки
============================================
Pydantic появился в 2019 году как инструмент валидации данных на основе Python type hints.
Изначально никакого AI — просто валидация входящих данных из внешних источников:
JSON из API, данные из форм, конфиги приложений.
Pydantic v2 по-прежнему живёт своей жизнью: FastAPI, Django, парсинг данных.

PydanticAI (2024) — это отдельная надстройка над Pydantic для работы с LLM.

ЗАЧЕМ PYDANTIC БЕЗ AI:
  Раньше:  data = json.loads(resp); age = int(data.get("age", 0))  ← точки отказа везде
  Теперь:  user = UserProfile(**data)  → ValidationError сразу при создании объекта

Слайды:   11-13 (проблема парсинга JSON), 15-20 (BaseModel как контракт)

Документация: https://docs.pydantic.dev/latest/
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from typing import Annotated
from annotated_types import Ge, Le
from datetime import date
import json


# =============================================================================
# ЧАСТЬ 1: BaseModel — базовый контракт данных
# Слайд 15: "BaseModel — это контракт, а не просто класс"
# =============================================================================

class MarketSignal(BaseModel):
    # Pydantic автоматически:
    # 1. Проверяет тип каждого поля
    # 2. Конвертирует "2024-01-15" (str) → date
    # 3. Конвертирует "100" (str) → int, если возможно
    # 4. Бросает ValidationError с точным путём к проблеме
    ticker: str
    signal: Literal["buy", "sell", "hold"]      # слайд 26: Literal — строго из списка
    confidence: float                             # 0.0 .. 1.0
    volume: int
    signal_date: date                             # автоконверсия "2024-01-15" → date

# Успешное создание — типы совпадают или конвертируются
s1 = MarketSignal(
    ticker="SBER",
    signal="buy",
    confidence=0.87,
    volume=150_000,
    signal_date="2024-05-01",   # строка → автоматически date
)
print(f"Создан сигнал: {s1.ticker} | {s1.signal} | уверенность={s1.confidence}")
print(f"Тип signal_date: {type(s1.signal_date)}")  # <class 'datetime.date'>, не str

# Ошибка: неверный тип — ValidationError сразу, не где-то в бизнес-логике
# (слайд 18: "Валидация при десериализации: ValidationError сразу")
try:
    bad = MarketSignal(
        ticker="GAZP",
        signal="URGENT",         # не входит в Literal["buy","sell","hold"]
        confidence="очень высокая",  # не float
        volume=50_000,
        signal_date="2024-05-01",
    )
except Exception as e:
    print(f"\nValidationError поймал:\n{e}")


# =============================================================================
# ЧАСТЬ 2: Field — документация + валидация + ограничения
# Слайд 20-21: "Field — это одновременно документация, валидация и промпт для модели"
# =============================================================================

class NewsItem(BaseModel):
    # Field(description=...) → попадает в JSON Schema → LLM видит это как подсказку
    # Field(ge=..., le=...) → числовые ограничения → Pydantic проверит после генерации
    # Field(max_length=...) → строковые ограничения
    # Field(pattern=...) → regex-валидация

    headline: str = Field(
        description="Заголовок новости на русском языке",
        max_length=200,
    )
    source: str = Field(
        description="Источник: название СМИ или тикер агентства",
    )
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        description="Настроение новости относительно рынка",
    )
    relevance_score: Annotated[int, Ge(1), Le(10)] = Field(
        description="Релевантность для трейдера 1-10",
    )
    ticker: Optional[str] = Field(
        default=None,
        description="Тикер компании если есть, иначе null",
        pattern=r"^[A-Z]{2,5}$",   # только заглавные буквы, 2-5 символов
    )

# JSON Schema генерируется автоматически из класса
# Именно эта схема уйдёт в OpenAI API как response_format (слайд 17)
schema = NewsItem.model_json_schema()
print("\nJSON Schema (что видит LLM):")
print(json.dumps(schema, ensure_ascii=False, indent=2))


# =============================================================================
# ЧАСТЬ 3: field_validator — нормализация и кастомная валидация
# Слайд 69 (три уровня валидации): уровень 2 — @field_validator внутри модели
# Кейс слайд 13: "$1,200.50" → 1200.50 — именно это делает field_validator
# =============================================================================

class TradeOrder(BaseModel):
    ticker: str
    amount: float   # может прийти как "$1,200.50" из LLM
    side: Literal["buy", "sell"]
    price: float

    @field_validator("amount", mode="before") # это только на этапе валидации поля amount, до того, как Pydantic попытается конвертировать значение в float. То есть, я ставлю тут ордер на покупку 1200.50 акций, и LLM может сгенерировать строку "$1,200.50" — этот валидатор сначала очистит её от символов валюты и разделителей тысяч, а уже потом передаст в стандартную конвертацию float, которая проверит, что это действительно число. То есть это дополнительная нормализация, которая позволяет LLM генерировать более человекопонятные строки, а Pydantic всё равно получает чистое число для валидации. Условно, если LLM несмотря на json schema дала не тот формат, то этот валидатор может попытаться его исправить, а если не получится — тогда уже будет ошибка при конвертации в float. Это своего рода "после генерации, но до стандартной валидации" этап, который позволяет гибко обрабатывать входные данные от LLM.
    @classmethod
    def normalize_amount(cls, v):
        # "mode=before" — запускается ДО стандартной pydantic-валидации - это что? ответ: до того, как Pydantic попытается конвертировать значение в float. Это позволяет нам сначала очистить строку от символов "$" и "," и только потом передать её в стандартную конвертацию float.
        # Именно здесь нормализуем строку от LLM к числу
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").strip()
            return float(cleaned)
            # то есть это способ получить от LLM строки ответа, где всё ещё есть символы валюты и разделители тысяч, и превратить их в чистое число, которое уже может быть валидировано как float стандартными средствами Pydantic.
            # но это же происходит на этапе валидации, то есть если LLM вернул строку, которая не соответствует формату, например "1.200,50" (европейский формат), то этот валидатор может не сработать и вызвать ошибку при попытке конвертации в float. Поэтому важно, чтобы LLM генерировал строки в ожидаемом формате.
        return v

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str: # а почему v? это стандартное имя аргумента для валидатора, который принимает значение поля. В данном случае, когда Pydantic обрабатывает поле "ticker", он передает его значение в этот метод как аргумент v. Это просто соглашение, и можно назвать его по-другому, например "value", но "v" — это кратко и часто используется в примерах Pydantic.
        # Всегда храним тикер в верхнем регистре
        return v.upper()

order = TradeOrder(
    ticker="sber",          # → "SBER"
    amount="$1,200.50",     # → 1200.50
    side="buy",
    price=265.40,
)
print(f"\nНормализованный ордер: {order.ticker} | {order.amount} | {order.side}")


# =============================================================================
# ЧАСТЬ 4: model_validator — проверка связей между полями
# Слайд 69: @field_validator для поля, model_validator для межполевых проверок
# =============================================================================

class DateRange(BaseModel):
    start: date
    end: date
    label: str

    @model_validator(mode="after")
    def end_after_start(self) -> "DateRange":
        # mode="after" — запускается ПОСЛЕ создания объекта
        # Проверяем связь между полями — это нельзя сделать в field_validator
        if self.end <= self.start:
            raise ValueError(
                f"end ({self.end}) должна быть позже start ({self.start})"
            )
        return self

# Ок
period = DateRange(start="2024-01-01", end="2024-12-31", label="Год 2024")
print(f"\nПериод: {period.start} — {period.end}")

# Ошибка: end раньше start
try:
    bad_period = DateRange(start="2024-12-31", end="2024-01-01", label="Плохой")
except Exception as e:
    print(f"Ошибка периода: {e}")


# =============================================================================
# ЧАСТЬ 5: Вложенные модели
# Слайд 23: "Вложенные схемы — агент думает структурно"
# Проблема плоского JSON: address_city, address_zip — плохо читается моделью
# Решение: вложенная модель Address → поле address: Address в основной
# =============================================================================

class Company(BaseModel):
    name: str
    inn: str = Field(pattern=r"^\d{10}$", description="ИНН 10 цифр")

class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class Invoice(BaseModel):
    supplier: Company             # вложенная модель!
    invoice_no: str
    invoice_date: date
    items: list[InvoiceItem]      # список вложенных объектов
    total: float
    vat: Optional[float] = None

# Pydantic рекурсивно валидирует вложенные объекты
# Ошибка в supplier.inn даст точный путь: "supplier.inn: ..."
invoice = Invoice(
    supplier=Company(name="ООО Ромашка", inn="7701234567"),
    invoice_no="2026-0417",
    invoice_date="2026-04-23",
    items=[
        InvoiceItem(description="Ноутбук Dell XPS", quantity=1, unit_price=185_000, total=185_000),
        InvoiceItem(description="Доставка", quantity=1, unit_price=1_500, total=1_500),
    ],
    total=186_500,
    vat=31_083.33,
)
print(f"\nСчёт: {invoice.supplier.name} | {invoice.invoice_no} | итого={invoice.total}")

# просто напомни, поля и атрибуты класса и объекта — это разные вещи. Поля класса — это то, что мы определяем в классе (например, name, inn в Company), а атрибуты объекта — это конкретные значения этих полей для каждого экземпляра класса. Когда мы создаём объект Company(name="ООО Ромашка", inn="7701234567"), мы передаём значения для полей name и inn, и эти значения становятся атрибутами этого конкретного объекта.
# В Pydantic, когда мы определяем поля в классе, мы фактически описываем структуру данных, которую ожидаем, а когда создаём экземпляр этого класса, мы заполняем эту структуру конкретными данными. И если эти данные не соответствуют типам или ограничениям, которые мы указали в полях класса, Pydantic выдаёт ошибку валидации.

# почему не через конструктор? потому что Pydantic позволяет создавать объекты не только через конструктор, но и через другие методы, например, через .parse_obj(), .from_json(), или даже автоматически при десериализации ответа от LLM. В любом случае, валидация будет работать, потому что она встроена в процесс создания объекта, независимо от того, какой метод мы используем для его создания. Это делает Pydantic очень гибким инструментом для работы с данными из разных источников, включая LLM, API и т.д.

# =============================================================================
# ЧАСТЬ 6: Discriminated Union — агент выбирает тип ответа
# Слайд 24: "Агент выбирает тип ответа"
# Применение: Success/Error паттерн, routing, multi-step reasoning
# =============================================================================

class BuySignal(BaseModel):
    status: Literal["buy"]      # discriminator поле
    ticker: str
    target_price: float
    stop_loss: float

class SellSignal(BaseModel):
    status: Literal["sell"]     # discriminator поле
    ticker: str
    reason: str

class NoSignal(BaseModel):
    status: Literal["hold"]
    message: str

# Union — LLM может вернуть любой из трёх типов
TradingDecision = BuySignal | SellSignal | NoSignal

# Pydantic автоматически определяет класс по полю status
raw_json = {"status": "buy", "ticker": "SBER", "target_price": 300.0, "stop_loss": 250.0}
decision = BuySignal(**raw_json)  # в PydanticAI это происходит автоматически

# После десериализации — типизированный объект с автодополнением IDE
if isinstance(decision, BuySignal):
    print(f"\nBuy: {decision.ticker} @ target={decision.target_price}, SL={decision.stop_loss}")


# =============================================================================
# ИТОГ:
# Pydantic (без AI) решает 3 задачи:
# 1. Валидация данных из внешних источников (JSON от LLM, API, формы)
# 2. Нормализация: "25" → 25, "$1,200.50" → 1200.50
# 3. Документация через Field(description=...) → JSON Schema для LLM
#
# Слайд 15: "Один класс BaseModel заменяет 15+ строк парсинга и 10+ unit-тестов"
# =============================================================================
print("\n✅ Pydantic basics — всё работает без AI, просто валидация данных")

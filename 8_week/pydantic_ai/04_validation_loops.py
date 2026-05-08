"""
ФАЙЛ 4: Validation Loops — три уровня проверки ответа LLM
==========================================================
Документация: https://ai.pydantic.dev/results/#output-validators
Слайды: 66–80
"""

# =============================================================================
# О ЧЁМ ЭТОТ ФАЙЛ?
#
# LLM может вернуть ответ, который:
#   — типически правильный (action="buy") но арифметически неверный
#     (trade_size_pct=5% когда target=12%, current=8%, должно быть 4%)
#   — не соответствует бизнес-правилу (critical без requires_human=True)
#   — содержит строку вместо числа ("265,40 ₽" вместо 265.40)
#
# Pydantic сам ловит ошибки типов. Но бизнес-логику нужно писать вручную.
# Для этого есть три уровня проверки — они выполняются последовательно:
#
#   Уровень 1 — JSON Schema (автоматически)
#     Pydantic проверяет типы, Literal, Annotated диапазоны.
#     Ошибка → LLM автоматически получает объяснение и пробует снова.
#
#   Уровень 2 — @field_validator (внутри класса)
#     Твой код для одного поля: нормализация, форматирование.
#     Пример: "265,40 ₽" → 265.40 (до того как Pydantic увидит значение).
#
#   Уровень 3 — @agent.output_validator (после агента)
#     Бизнес-правила, которые нельзя выразить типами.
#     Пример: trade_size_pct = |target - current| — арифметика между полями.
#     Есть доступ к ctx.deps — можно проверять лимиты роли.
#
# ЦИКЛ: Generate → Validate → OK? вернуть / Fail? ModelRetry → Generate...
#       После retries=N → UnexpectedModelBehavior (circuit breaker)
# =============================================================================

import asyncio
from dataclasses import dataclass
from datetime import date
from typing import Literal, Annotated
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior
from annotated_types import Ge, Le
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# УРОВЕНЬ 2: @field_validator — нормализация строк от LLM
#
# ЧТО ЕСТЬ: LLM иногда возвращает "265,40 ₽" вместо числа 265.40.
#            В реальных случаях это приводит к ошибкам расчёта (слайд 13).
# ЧТО ДЕЛАЕМ: добавляем @field_validator с mode="before" — он срабатывает
#              ДО того как Pydantic попытается привести тип.
# КАК РАБОТАЕТ:
#   1. LLM возвращает: {"price": "265,40 ₽", "ticker": "sber"}
#   2. Pydantic вызывает normalize_money("265,40 ₽") → 265.4
#   3. Pydantic вызывает validate_ticker("sber") → "SBER"
#   4. Только потом проверяет типы — всё уже чистое
#   mode="before" = запустить валидатор ДО приведения типа
#   mode="after"  = запустить валидатор ПОСЛЕ приведения типа (default)
# =============================================================================

class TradeExecution(BaseModel):
    ticker: str
    quantity: int = Field(ge=1, description="Количество лотов")
    price: float = Field(description="Цена за лот в рублях")
    commission: float = Field(default=0.0, description="Комиссия брокера")
    execution_date: date

    @field_validator("price", "commission", mode="before")
    @classmethod
    def normalize_money(cls, v):
        """Убираем валютные символы и нормализуем разделитель."""
        if isinstance(v, str):
            cleaned = (v.replace("₽", "").replace("$", "")
                       .replace(",", ".").replace(" ", "").strip())
            return float(cleaned)
        return v

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper().strip()


# Запускается при импорте — показывает что нормализация работает без LLM
trade = TradeExecution(
    ticker="sber",
    quantity=100,
    price="265,40 ₽",   # строка с запятой — нормализуется в 265.4
    commission="0.05",
    execution_date="2024-05-01",
)
print(f"Trade: {trade.ticker} x{trade.quantity} @ {trade.price} руб.")


# =============================================================================
# УРОВЕНЬ 3: @output_validator — бизнес-логика между полями
#
# ЧТО ЕСТЬ: @field_validator проверяет одно поле изолированно.
# ПРОБЛЕМА: иногда нужно проверить СООТВЕТСТВИЕ нескольких полей друг другу.
#   Пример: если target=12% и current=8%, то trade_size_pct ОБЯЗАН быть 4%.
#   LLM иногда считает неправильно или округляет — нам нужна арифметическая проверка.
# ЧТО ДЕЛАЕМ: добавляем @rebalance_agent.output_validator — функцию, которая
#              PydanticAI вызывает ПОСЛЕ того как все типы уже проверены.
# КАК РАБОТАЕТ:
#   1. LLM возвращает PortfolioRebalance(target=12%, current=8%, trade_size=5%)
#   2. Pydantic проверяет типы — всё OK (5% это float от 0 до 100)
#   3. PydanticAI вызывает validate_rebalance()
#   4. Мы считаем: expected = |12-8| = 4%, но got = 5% → raise ModelRetry
#   5. LLM получает: "trade_size_pct (5.0%) должен равняться 4.0%. Исправь."
#   6. LLM исправляет и возвращает правильный ответ
#
# Слайд 69: @output_validator — третий рубеж, после JSON Schema и field_validator
# =============================================================================

@dataclass
class PortfolioDeps:
    user_id: str
    role: Literal["analyst", "trader", "manager"]
    max_position_pct: float   # максимальная доля одной позиции в портфеле, %
    portfolio_value: float    # текущая стоимость портфеля в рублях


class PortfolioRebalance(BaseModel):
    # Поля в порядке рассуждений: сначала факты, потом решение
    rationale: str = Field(max_length=300, description="Обоснование")
    ticker: str
    current_weight_pct: float = Field(ge=0, le=100, description="Текущая доля в %")
    target_weight_pct: float = Field(ge=0, le=100, description="Целевая доля в %")
    trade_direction: Literal["increase", "decrease", "keep"]
    trade_size_pct: float = Field(ge=0, le=100, description="Изменение доли в %")
    risk_note: str = Field(max_length=200)


rebalance_agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=PortfolioRebalance,
    deps_type=PortfolioDeps,
    retries=3,
    system_prompt="""Ты советник по управлению портфелем.
trade_size_pct = abs(target_weight_pct - current_weight_pct).
trade_direction: increase если target > current, decrease если target < current.""",
)


@rebalance_agent.output_validator
async def validate_rebalance(
    ctx: RunContext[PortfolioDeps],
    output: PortfolioRebalance,
) -> PortfolioRebalance:
    errors = []

    # Проверка 1: арифметика — trade_size_pct должен совпадать с разницей весов
    expected_size = abs(output.target_weight_pct - output.current_weight_pct)
    if abs(output.trade_size_pct - expected_size) > 0.1:
        errors.append(
            f"trade_size_pct ({output.trade_size_pct:.1f}%) должен равняться "
            f"|{output.target_weight_pct:.1f}% - {output.current_weight_pct:.1f}%| "
            f"= {expected_size:.1f}%. Исправь."
        )

    # Проверка 2: направление соответствует изменению веса
    if output.target_weight_pct > output.current_weight_pct and output.trade_direction != "increase":
        errors.append(
            f"target > current → trade_direction должен быть 'increase', "
            f"не '{output.trade_direction}'."
        )
    elif output.target_weight_pct < output.current_weight_pct and output.trade_direction != "decrease":
        errors.append(
            f"target < current → trade_direction должен быть 'decrease', "
            f"не '{output.trade_direction}'."
        )

    # Проверка 3: лимит позиции из deps — защита в коде, не в промпте
    if output.target_weight_pct > ctx.deps.max_position_pct:
        errors.append(
            f"target_weight_pct ({output.target_weight_pct:.1f}%) превышает лимит "
            f"{ctx.deps.max_position_pct:.1f}% для роли '{ctx.deps.role}'. "
            f"Уменьши target_weight_pct до {ctx.deps.max_position_pct:.1f}% или ниже."
        )

    if errors:
        # Слайд 73: ModelRetry — пиши информативно.
        # Плохо: raise ModelRetry("Invalid data")
        # Хорошо: raise ModelRetry(f"trade_size_pct ({got}) должен быть {expected}")
        raise ModelRetry("\n".join(errors))

    return output


async def demo_output_validator():
    deps = PortfolioDeps(
        user_id="trader_01",
        role="trader",
        max_position_pct=15.0,
        portfolio_value=10_000_000,
    )
    result = await rebalance_agent.run(
        "SBER сейчас 8% портфеля. Рост доходов 20%. Рекомендую увеличить до 12%.",
        deps=deps,
    )
    r = result.output
    print(f"\nРебалансировка: {r.ticker}")
    print(f"  {r.current_weight_pct}% → {r.target_weight_pct}%  ({r.trade_direction} {r.trade_size_pct}%)")
    print(f"  Retries: {result.usage().requests - 1}")


# =============================================================================
# SUMMARY — зачем нужен @output_validator
#
# Ты получил типизированный ответ от LLM — все поля правильного типа.
# Но LLM мог сделать логическую ошибку внутри ответа или нарушить
# бизнес-правило, которое нельзя выразить типом.
#
# @output_validator — это твой код, который запускается ВСЕГДА после каждого
# ответа LLM. Здесь ты:
#   — проверяешь соответствие полей друг другу  (action="buy" но size_usd=0)
#   — проверяешь бизнес-правила               (critical → requires_human=True)
#   — проверяешь лимиты из deps         (target_weight > ctx.deps.max_position_pct)
#   — сверяешь с реальными данными                       (цена в БД vs ответ LLM)
#
# Если что-то не так → raise ModelRetry("объясни что именно и как исправить")
# LLM читает, исправляет конкретные поля и возвращает новый ответ.
# =============================================================================


# =============================================================================
# CIRCUIT BREAKER: что происходит когда retries кончаются
#
# ЧТО ЕСТЬ: @output_validator поднимает ModelRetry → LLM пробует снова.
# ПРОБЛЕМА: что если LLM так и не исправит ответ за N попыток?
# ЧТО ДЕЛАЕМ: ловим UnexpectedModelBehavior в try/except и возвращаем
#              безопасный fallback вместо крэша всего приложения.
# КАК РАБОТАЕТ:
#   retries=2 → значит 2 ДОПОЛНИТЕЛЬНЫЕ попытки (итого 3 запроса к LLM).
#   После третьей неудачи → PydanticAI поднимает UnexpectedModelBehavior.
#   Это НЕ баг — это намеренный circuit breaker (слайд 75).
#   "Явная ошибка лучше тихого неправильного ответа."
# =============================================================================

class MarketAlert(BaseModel):
    alert_type: Literal["price_spike", "volume_surge", "news_break"]
    severity: Literal["low", "medium", "high", "critical"]
    ticker: str
    description: str = Field(max_length=150)
    requires_immediate_action: bool


alert_agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=MarketAlert,
    retries=2,
    system_prompt="Генерируй рыночные алерты строго по схеме.",
)


@alert_agent.output_validator
async def validate_alert(ctx: RunContext[None], output: MarketAlert) -> MarketAlert:
    # Бизнес-правило: critical → requires_immediate_action обязан быть True
    if output.severity == "critical" and not output.requires_immediate_action:
        raise ModelRetry(
            "severity='critical' требует requires_immediate_action=True. "
            "Critical алерт — всегда немедленное действие. Исправь."
        )
    return output


async def demo_circuit_breaker():
    try:
        result = await alert_agent.run(
            "Акции SBER упали на 15% за 5 минут — массовая продажа"
        )
        r = result.output
        print(f"\nАлерт: {r.alert_type} | {r.severity}")
        print(f"Немедленное действие: {r.requires_immediate_action}")
        print(f"Retries использовано: {result.usage().requests - 1}")

    except UnexpectedModelBehavior as e:
        # LLM не смог выполнить требование после всех попыток
        print(f"❌ Агент упал после исчерпания retries: {e}")
        # В production: logger.error(...) + возврат безопасного дефолта
        fallback = MarketAlert(
            alert_type="price_spike",
            severity="high",   # понижаем критичность, ставим human=True
            ticker="SBER",
            description="Автогенерация не удалась — нужна ручная проверка",
            requires_immediate_action=True,
        )
        print(f"Fallback: {fallback}")


# =============================================================================
# ВСЕ ТРИ УРОВНЯ В ОДНОЙ МОДЕЛИ
#
# ЧТО ЕСТЬ: три отдельных примера выше.
# ЧТО ДЕЛАЕМ: собираем все три уровня в одну модель — чтобы видеть порядок.
# КАК РАБОТАЕТ: Pydantic применяет уровни строго по порядку:
#   1 → JSON Schema:      signal_strength — Annotated[float, Ge(0), Le(1)]
#                          entry_price, stop_loss, take_profit — Field(ge=0)
#   2 → @field_validator: ticker → верхний регистр
#   3 → @output_validator: take_profit > entry_price, stop_loss < entry_price,
#                          risk_reward перепроверяем сами (LLM плохо считает)
# =============================================================================

class SignalReport(BaseModel):
    ticker: str
    signal_strength: Annotated[float, Ge(0.0), Le(1.0)]  # уровень 1
    entry_price: float = Field(ge=0)
    stop_loss: float = Field(ge=0)
    take_profit: float = Field(ge=0)
    risk_reward: float

    @field_validator("ticker")                            # уровень 2
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper()


signal_agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=SignalReport,
    retries=2,
    system_prompt="""Генерируй торговые сигналы.
risk_reward = (take_profit - entry_price) / (entry_price - stop_loss).
take_profit > entry_price. stop_loss < entry_price.""",
)


@signal_agent.output_validator                            # уровень 3
async def validate_signal(ctx: RunContext[None], output: SignalReport) -> SignalReport:
    if output.take_profit <= output.entry_price:
        raise ModelRetry(
            f"take_profit ({output.take_profit}) должен быть БОЛЬШЕ "
            f"entry_price ({output.entry_price})."
        )
    if output.stop_loss >= output.entry_price:
        raise ModelRetry(
            f"stop_loss ({output.stop_loss}) должен быть МЕНЬШЕ "
            f"entry_price ({output.entry_price})."
        )
    # LLM плохо считает арифметику — пересчитываем сами и сравниваем
    computed_rr = (output.take_profit - output.entry_price) / (output.entry_price - output.stop_loss)
    if abs(output.risk_reward - computed_rr) > 0.1:
        raise ModelRetry(
            f"risk_reward = (TP-entry)/(entry-SL) = {computed_rr:.2f}, "
            f"а не {output.risk_reward:.2f}. Исправь."
        )
    return output


async def demo_three_levels():
    result = await signal_agent.run(
        "YNDX: пробой уровня 3900. Текущая цена 3912. Стоп 3850. Цель 4100."
    )
    r = result.output
    print(f"\nСигнал: {r.ticker}")
    print(f"  Entry: {r.entry_price} | SL: {r.stop_loss} | TP: {r.take_profit}")
    print(f"  R/R: {r.risk_reward:.2f} | Сила: {r.signal_strength:.0%}")
    print(f"  Retries: {result.usage().requests - 1}")


# =============================================================================
# ИТОГ — три уровня и когда каждый применять
#
# @field_validator  — один поле, нормализация, mode="before" если строка→число
# @output_validator — несколько полей, бизнес-правила, доступ к deps
# ModelRetry        — сообщение для LLM, пиши точно: что не так и как исправить
# retries=N         — сколько раз LLM может исправить ответ
# UnexpectedModelBehavior — circuit breaker: ловить в try/except, возвращать fallback
# =============================================================================

if __name__ == "__main__":
    # asyncio.run(demo_output_validator())
    # asyncio.run(demo_circuit_breaker())
    asyncio.run(demo_three_levels())

"""
ФАЙЛ 2: Agent + output_type — Schema-First подход
==================================================
Главная идея PydanticAI: НЕ просить LLM "верни JSON", а передать схему
как response_format → модель физически не может нарушить структуру.

Цепочка (слайд 42):
  Input → [Agent + output_type] → [LLM получает JSON Schema] → [constrained decoding]
         → [Pydantic валидирует ответ] → Typed Output (result.output)

Три уровня надёжности (слайды 5-10):
  Level 1 (Prompt Engineering):      80-95%  — просим, но не гарантируем
  Level 2 (Function Calling):        95-99%  — схема как hint
  Level 3 (Native Structured Output): 100%   — FSM маскирует невалидные токены

PydanticAI использует Level 3 когда провайдер поддерживает (OpenAI, Anthropic).

Документация: https://ai.pydantic.dev/results/
"""

import asyncio
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import Literal, Optional
from typing import Annotated
from annotated_types import Ge, Le

# PydanticAI сам читает ANTHROPIC_API_KEY из окружения — передавать клиент не нужно.
# Достаточно положить ANTHROPIC_API_KEY=sk-ant-... в файл .env рядом с этим скриптом.
load_dotenv()

# =============================================================================
# ПРИМЕР 1: Простейший агент с типизированным выводом
# Слайд 22: "output_type=CityInfo — агент знает что должен вернуть"
# result.output.population — это уже int, не string
# =============================================================================

class AssetInfo(BaseModel):
    # Все поля типизированы — result.output.market_cap будет float, не строкой
    name: str = Field(description="Полное название компании")
    ticker: str = Field(description="Биржевой тикер, заглавные буквы")
    sector: str = Field(description="Сектор экономики")
    market_cap_usd_bn: float = Field(description="Рыночная капитализация в млрд USD")
    founded_year: int = Field(ge=1800, le=2030)
    country: str = Field(description="Страна регистрации, ISO код (RU, US, DE...)")

# Agent объявляется с output_type — это контракт вывода
# PydanticAI автоматически: генерирует JSON Schema из AssetInfo
#                           передаёт как response_format в API запрос
#                           валидирует ответ → result.output типизирован
asset_agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=AssetInfo,
    system_prompt="Ты финансовый аналитик. Отвечай точно по схеме.",
)


async def demo_simple():
    # result.output — это AssetInfo объект, не dict и не строка
    result = await asset_agent.run("Расскажи о Yandex")
    r = result.output

    # IDE знает тип → автодополнение работает
    print(f"Компания: {r.name}")
    print(f"Тикер: {r.ticker}")           # str — гарантировано
    print(f"Капитализация: {r.market_cap_usd_bn} млрд USD")  # float — не "около 100 млрд"
    print(f"Токены: {result.usage().total_tokens}")

'''
Компания: Yandex
Тикер: YNDX
Капитализация: 18.5 млрд USD
Токены: 1412
'''

# =============================================================================
# ПРИМЕР 2: Literal — строго из списка значений
# Слайд 25: "Literal — агент выбирает из списка"
# Проблема без Literal: "buy", "Buy", "recommend buying", "should buy" — всё разное
# С Literal — физически невозможно вернуть что-то другое (constrained decoding)
# =============================================================================

class NewsClassification(BaseModel):
    # Schema-Guided Reasoning (слайд 44): поля в порядке рассуждений модели
    # 1. Сначала summary (понять о чём) 2. Потом sentiment 3. Потом impact
    summary: str = Field(
        max_length=150,
        description="Краткое резюме новости для трейдера",
    )
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        description="Влияние на рынок: bullish=рост, bearish=падение, neutral=нейтрально",
    )
    affected_sector: Literal[
        "energy", "finance", "tech", "consumer", "industrial", "other"
    ] = Field(description="Затронутый сектор экономики")
    urgency: Annotated[int, Ge(1), Le(5)] = Field(
        description="Срочность для трейдера: 1=обычная новость, 5=торговать немедленно",
    )
    related_ticker: Optional[str] = Field(
        default=None,
        description="Тикер компании если конкретная, иначе null",
    )
    requires_action: bool = Field(
        description="True если требует немедленного внимания трейдера",
    )

news_agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=NewsClassification,
    system_prompt="""Ты классифицируешь финансовые новости для трейдера.
Оценивай влияние на рынок акций. Будь точен и конкретен.""",
)


async def demo_news():
    test_news = [
        "Нефть падает на слухах об окончании войны с Ираном",
        "Apple анонсировала новый iPhone 17 на конференции WWDC",
    ]

    for news in test_news:
        result = await news_agent.run(news)
        r = result.output
        print(f"\nНовость: {news[:50]}...")
        print(f"  sentiment: {r.sentiment}")     # строго bullish/bearish/neutral
        print(f"  urgency: {r.urgency}/5")       # строго int 1-5
        print(f"  action: {r.requires_action}")  # строго bool


# =============================================================================
# ПРИМЕР 3: Discriminated Union — агент выбирает тип ответа
# Слайд 24: два разных класса ответа по полю status
# Применение: когда агент может ответить успехом ИЛИ ошибкой с разными полями
# =============================================================================

class AnalysisSuccess(BaseModel):
    status: Literal["success"]
    ticker: str
    currenet_price: float = Field('текущая цена в Rub')
    recommendation: Literal["buy", "sell", "hold"]
    price_target: float = Field('целевое значение цены в Rub')
    reasoning: str = Field(max_length=300)

class AnalysisError(BaseModel):
    status: Literal["error"]
    reason: str
    suggestion: str   # что сделать пользователю

AnalysisResult = AnalysisSuccess | AnalysisError

analysis_agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=AnalysisResult,   # тип: Union двух классов
    system_prompt="""Анализируй акции. Если запрос непонятен или тикер неизвестен —
верни статус error с объяснением.""",
)


async def demo_union():
    queries = [
        "Проанализируй YNDX для долгосрочного инвестирования",
        "Что скажешь про акции 'Рога и Копыта ООО'?",
    ]

    for query in queries:
        result = await analysis_agent.run(query)
        r = result.output

        # Discriminated Union — match по status
        match r.status:
            case "success":
                assert isinstance(r, AnalysisSuccess)
                print(f"\n✅ {r.ticker}: {r.recommendation} @ {r.price_target}")
            case "error":
                assert isinstance(r, AnalysisError)
                print(f"\n❌ Ошибка: {r.reason}")
                print(f"   Совет: {r.suggestion}")


# =============================================================================
# ПРИМЕР 4: Schema-Guided Reasoning
# Слайд 44-46: порядок полей в BaseModel = порядок рассуждений модели
#
# Обычный промпт → произвольный текст → нельзя обработать автоматически
# SGR: схема определяет шаги рассуждений → модель вынуждена пройти все шаги
# =============================================================================

class MarketAnalysis(BaseModel):
    # Порядок полей = chain-of-thought (слайд 44)
    # 1. Сначала собрать факты (facts_summary)
    # 2. Оценить риски (risk_level)
    # 3. Определить временной горизонт (horizon)
    # 4. Только потом — рекомендация (recommendation)
    # Модель проходит поля последовательно → качество растёт
    facts_summary: str = Field(
        description="Ключевые факты для анализа (2-3 предложения)",
        max_length=300,
    )
    key_risks: list[str] = Field(
        description="Список основных рисков (2-4 пункта)",
        max_length=4,   # не более 4 рисков
    )
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        description="Общий уровень риска инвестиции",
    )
    horizon: Literal["short", "medium", "long"] = Field(
        description="Рекомендуемый горизонт: short=до 3мес, medium=3-12мес, long=1+ год",
    )
    recommendation: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"] = Field(
        description="Итоговая рекомендация — ТОЛЬКО после анализа всех предыдущих полей",
    )
    confidence: Annotated[float, Ge(0.0), Le(1.0)] = Field(
        description="Уверенность в рекомендации от 0.0 до 1.0",
    )

sgr_agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=MarketAnalysis,
    system_prompt="""Ты старший аналитик. Анализируй последовательно:
факты → риски → уровень риска → горизонт → рекомендация.""",
)


async def demo_sgr():
    result = await sgr_agent.run(
        "урановая энергетика накормит?"
    )
    r = result.output
    print(f"\nFacts: {r.facts_summary}")
    print(f"Risks: {r.key_risks}")
    print(f"Risk level: {r.risk_level}")
    print(f"Horizon: {r.horizon}")
    print(f"→ {r.recommendation} (confidence: {r.confidence})")


# =============================================================================
# КАК ЗАПУСКАТЬ (в Jupyter/Colab):
#   result = await asset_agent.run("Расскажи о SBER")
#
# В обычном .py файле:
#   asyncio.run(demo_simple())
# =============================================================================

if __name__ == "__main__":
    # asyncio.run(demo_simple())
    # asyncio.run(demo_news())
    # asyncio.run(demo_union())
    asyncio.run(demo_sgr())

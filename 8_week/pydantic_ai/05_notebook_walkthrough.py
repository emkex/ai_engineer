"""
ФАЙЛ 5: Разбор pydantic.ipynb — построчные пояснения
======================================================
Это разбор практики из ноутбука 8_week/pydantic.ipynb.
Каждый блок ноутбука разобран по строкам с объяснением ЗАЧЕМ и КАК.

СТРУКТУРА НОУТБУКА:
  Cell 0: Install + setup
  Cell 1: TicketClassification + TicketDeps — схемы данных
  Cell 2: Agent + escalate_ticket tool + output_validator
  Cell 3: Запуск одного тикета
  Cell 4: Пакетный запуск 5 тикетов
  Cell 5: Сохранение в Google Sheets

ФИНАЛЬНАЯ АРХИТЕКТУРА (слайд Production-ready, слайд 79):
  Схема (контракт) + Deps (контекст) + Validation (защита) = агент не ломает prod
"""

# =============================================================================
# CELL 1 РАЗБОР: TicketClassification + TicketDeps
# =============================================================================

from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
from pydantic import BaseModel, Field
from typing import Literal, Annotated
from annotated_types import Ge, Le


# --- TicketClassification ---
# Это OUTPUT TYPE — контракт вывода агента (слайд 15-16).
# LLM получит JSON Schema из этого класса как response_format.
# result.output будет объектом TicketClassification, не dict.
class TicketClassification(BaseModel):
    # Literal — строго из 4 значений, не "Billing", не "billing issue" (слайд 25)
    category: Literal["billing", "technical", "account", "other"]

    # Literal — строго из 4 значений. Constrained decoding не даст выйти за список.
    priority: Literal["low", "medium", "high", "critical"]

    # Field(max_length=100) — ограничение длины. Попадёт в JSON Schema → LLM знает лимит.
    summary: str = Field(max_length=100)

    # bool — строго True/False, не "yes" и не "maybe"
    requires_human: bool

    # Annotated[int, Ge(1), Le(480)] — целое число от 1 до 480 минут.
    # Ge/Le из annotated_types — более строгий синтаксис чем Field(ge=...).
    # Эквивалент: Field(ge=1, le=480) — оба варианта работают.
    estimated_minutes: Annotated[int, Ge(1), Le(480)]


# --- TicketDeps ---
# Это ЗАВИСИМОСТИ агента — контекст без промпта (блок 3 презентации, слайды 53-65).
# Не @dataclass class vs class BaseModel:
#   @dataclass — для зависимостей (нет валидации Pydantic, просто контейнер данных)
#   BaseModel  — для output_type (нужна Pydantic-валидация)
@dataclass
class TicketDeps:
    user_id: str

    # Literal здесь — статическая типизация. mypy/pyright поймают неверный role при сборке.
    role: Literal["agent", "supervisor"]

    # max_priority — лимит роли. agent не может установить critical.
    # Хранится в deps, НЕ в системном промпте → нельзя обойти prompt injection.
    max_priority: Literal["low", "medium", "high", "critical"]


# Словарь для сравнения приоритетов по числовому рангу
# Используется в инструменте escalate_ticket для сравнения
PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


# =============================================================================
# CELL 2 РАЗБОР: Agent + escalate_ticket + output_validator
# =============================================================================

# --- Agent ---
# output_type=TicketClassification → PydanticAI:
#   1. Генерирует JSON Schema из TicketClassification
#   2. Передаёт как response_format в OpenAI API
#   3. После ответа валидирует через Pydantic
#   4. Если не прошло → RetryPromptPart → модель исправляет
#
# deps_type=TicketDeps → объявляем тип зависимостей для статической проверки
# retries=3 → максимум 3 попытки при ModelRetry (суммарно для tools + validator)
agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    output_type=TicketClassification,
    deps_type=TicketDeps,
    retries=3,
    system_prompt="""Ты классифицируешь тикеты поддержки.
Если тикет требует эскалации — вызови инструмент escalate_ticket.

КРИТЕРИИ ПРИОРИТЕТА:
- critical: взлом аккаунта, полный сбой API, финансовые потери прямо сейчас
- high: двойное списание, невозможно войти, API 500, интеграция сломана
- medium: частичные ошибки, задержки, нужна помощь с настройкой
- low: вопросы как-сделать, запросы на изменение тарифа, пожелания

ВАЖНО:
- Если priority=critical, то requires_human ОБЯЗАТЕЛЬНО должно быть true
- estimated_minutes должно быть кратно 15 (15, 30, 45, 60, 90, 120...)""",
)


# --- @agent.tool: escalate_ticket ---
# Инструмент — функция которую LLM может вызвать когда считает нужным.
# ctx: RunContext[TicketDeps] — доступ к deps.role и deps.max_priority
#
# ЗАЧЕМ ИНСТРУМЕНТ, А НЕ ПРОСТО ПРОВЕРКА В ПРОМПТЕ:
# Слайд 59: "если security-критично — это должно быть в коде (deps+tool), а не в промпте"
# Промпт: "agents cannot set critical" → можно обойти prompt injection
# Tool:   if PRIORITY_RANK[new_priority] > max_rank: raise ModelRetry(...)  → код, не слова
@agent.tool
async def escalate_ticket(
    ctx: RunContext[TicketDeps],
    ticket_id: str,
    new_priority: Literal["low", "medium", "high", "critical"],
) -> str:
    # Получаем числовой ранг максимально допустимого приоритета из deps
    max_rank = PRIORITY_RANK[ctx.deps.max_priority]

    # Проверяем: не превышает ли запрошенный приоритет лимит роли
    if PRIORITY_RANK[new_priority] > max_rank:
        # ModelRetry — не исключение приложения, а сообщение для LLM.
        # Слайд 73: пишем информативно — модель должна знать что исправить.
        raise ModelRetry(
            f"Role '{ctx.deps.role}' не может установить priority '{new_priority}'. "
            f"Максимально допустимый: '{ctx.deps.max_priority}'. "
            f"Используй '{ctx.deps.max_priority}' или ниже."
        )
    # Если OK — возвращаем строку подтверждения.
    # LLM видит эту строку как результат tool call и продолжает работу.
    return f"✅ Ticket {ticket_id} escalated to '{new_priority}' by {ctx.deps.role}"


# --- @agent.output_validator ---
# Вызывается ПОСЛЕ того как Pydantic проверил типы.
# Здесь проверяем БИЗНЕС-ЛОГИКУ, которую нельзя выразить в типах.
#
# Три уровня (слайд 69):
#   1. Pydantic types → уже проверено (Literal, Annotated int 1-480, bool)
#   2. @field_validator → в этом примере не используется
#   3. @output_validator → мы здесь
validation_log = []  # глобальный лог для демонстрации — в проде используй логгер


@agent.output_validator
async def validate_output(
    ctx: RunContext[TicketDeps],
    output: TicketClassification,
) -> TicketClassification:
    errors = []

    # Проверка 1: Бизнес-правило — critical требует human review
    # Это нельзя выразить в типах: Pydantic не знает о связи priority и requires_human.
    if output.priority == "critical" and not output.requires_human:
        msg = (
            f"priority='critical' но requires_human=False. "
            f"Critical тикеты ОБЯЗАНЫ иметь requires_human=True."
        )
        validation_log.append({"check": 1, "status": "RETRY", "msg": msg})
        errors.append(msg)

    # Проверка 2: estimated_minutes должно быть кратно 15
    # Это бизнес-правило процесса поддержки — слоты по 15 минут.
    # Pydantic проверил что это int от 1 до 480, но кратность — наша задача.
    if output.estimated_minutes % 15 != 0:
        rounded = round(output.estimated_minutes / 15) * 15
        rounded = max(15, min(480, rounded))  # держим в допустимом диапазоне
        msg = (
            f"estimated_minutes={output.estimated_minutes} не кратно 15. "
            f"Используй {rounded} (ближайшее кратное 15)."
        )
        validation_log.append({"check": 2, "status": "RETRY", "msg": msg})
        errors.append(msg)

    if errors:
        # ModelRetry с несколькими ошибками — LLM исправит все сразу
        raise ModelRetry("\n".join(errors))

    # Всё OK — логируем успех и возвращаем неизменённый output
    validation_log.append({
        "check": "all",
        "status": "PASS",
        "priority": output.priority,
        "requires_human": output.requires_human,
        "estimated_minutes": output.estimated_minutes,
    })
    return output


# =============================================================================
# CELL 3 РАЗБОР: Запуск одного тикета
# =============================================================================

async def run_single_ticket():
    validation_log.clear()

    ticket_text = "Мой аккаунт был взломан, вижу подозрительные входы из другой страны"

    # deps — типизированный контекст. supervisor может устанавливать critical.
    deps = TicketDeps(
        user_id="supervisor_01",
        role="supervisor",
        max_priority="critical",  # supervisor может всё
    )

    result = await agent.run(ticket_text, deps=deps)
    r = result.output

    print(f"Тикет: {ticket_text}")
    print(f"Категория: {r.category}")
    print(f"Приоритет: {r.priority}")
    print(f"Требует человека: {r.requires_human}")
    print(f"Время (минуты): {r.estimated_minutes}")
    print(f"Резюме: {r.summary}")

    # result.usage().requests — сколько LLM-запросов было сделано
    # Если retries сработали — requests > 1
    retries_used = result.usage().requests - 1
    print(f"Retries: {retries_used}")


# =============================================================================
# CELL 4 РАЗБОР: Пакетный запуск + проверка инвариантов
# =============================================================================

async def run_batch():
    """Запускает несколько тикетов и проверяет инварианты."""
    test_tickets = [
        # (текст тикета, роль, max_priority)
        ("Взлом аккаунта, чужие входы из другой страны", "supervisor", "critical"),
        ("API возвращает 500 при запросе с токеном", "supervisor", "critical"),
        ("Не могу войти в аккаунт — неверный пароль", "agent", "high"),
        ("Как изменить валюту выставления счетов?", "agent", "high"),
        ("Приложение медленно загружается", "agent", "high"),
    ]

    validation_log.clear()
    results = []

    for ticket_text, role, max_p in test_tickets:
        deps = TicketDeps(
            user_id=f"user_{role}",
            role=role,
            max_priority=max_p,
        )
        res = await agent.run(ticket_text, deps=deps)
        r = res.output

        # Финальная проверка инвариантов — assert как "дымовой тест"
        # Если output_validator работает правильно, assert никогда не сработает
        assert not (r.priority == "critical" and not r.requires_human), \
            "ИНВАРИАНТ НАРУШЕН: critical без requires_human!"
        assert r.estimated_minutes % 15 == 0, \
            f"ИНВАРИАНТ НАРУШЕН: {r.estimated_minutes} не кратно 15!"

        results.append({
            "ticket": ticket_text[:40] + "...",
            "priority": r.priority,
            "requires_human": r.requires_human,
            "est_minutes": r.estimated_minutes,
            "retries": res.usage().requests - 1,
            "invariants_ok": "✅",
        })
        print(f"✅ {ticket_text[:45]}... → {r.priority} | human={r.requires_human}")

    print(f"\n✅ Все {len(results)} тикетов обработаны, инварианты соблюдены")
    return results


# =============================================================================
# CELL 5 ЛОГИКА (без Google Sheets для локального запуска):
# В ноутбуке — запись в Google Sheets через gspread.
# В production — запись в БД через deps (см. файл 03_dependencies.py).
# =============================================================================

def format_report(results: list) -> str:
    """Форматирует результаты для отображения / записи."""
    lines = ["ticket | priority | human | minutes | retries | ok"]
    for r in results:
        lines.append(
            f"{r['ticket'][:30]} | {r['priority']:8} | {r['requires_human']} | "
            f"{r['est_minutes']:3} | {r['retries']} | {r['invariants_ok']}"
        )
    return "\n".join(lines)


# =============================================================================
# КЛЮЧЕВЫЕ ПАТТЕРНЫ НОУТБУКА — итог
# =============================================================================
#
# 1. SCHEMA AS CONTRACT (слайд 16):
#    TicketClassification(BaseModel) = единственное определение формата.
#    LLM получает JSON Schema → constrained decoding → 100% соответствие.
#
# 2. DEPS НЕ В ПРОМПТЕ (слайд 54):
#    role и max_priority в TicketDeps, а не в f"You have role {role}..."
#    → нельзя обойти prompt injection
#    → легко тестировать через fake deps
#
# 3. VALIDATION LOOP (слайд 67-68):
#    output_validator проверяет бизнес-правила ПОСЛЕ Pydantic type check.
#    ModelRetry с точным сообщением → модель исправляет с первой попытки.
#
# 4. RETRIES = SAFETY NET (слайд 75):
#    retries=3 → максимум 3 попытки.
#    result.usage().requests - 1 = сколько раз пришлось исправлять.
#    В норме: 0 retries. 1 retry — нормально. 2+ — смотри промпт.
#
# 5. ИНВАРИАНТЫ ≠ ВАЛИДАЦИЯ (слайды 78-79):
#    assert после run() — это дымовой тест что система работает.
#    Не замена output_validator — assert уже не вернёт LLM на исправление.

if __name__ == "__main__":
    import asyncio
    # asyncio.run(run_single_ticket())
    # asyncio.run(run_batch())
    print("Раскомментируй нужную функцию и установи ANTHROPIC_API_KEY")

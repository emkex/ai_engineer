"""
browser-use 0.12.x с локальными моделями Ollama.

Почему llama3.2 (3B) не работает с browser-use:
  browser-use требует строго форматированный JSON-вывод действий.
  3B модели не умеют стабильно следовать такой схеме → 1 шаг и падение.

Что помогает:
  1. gemma3:4b — лучше llama3.2 в instruction following
  2. flash_mode=True — упрощённый формат вывода для слабых моделей
     (убирает plan_update, сокращает схему)

Реальный минимум для browser-use: 7B+ с хорошим instruction tuning.
Рабочие варианты: qwen2.5:7b, mistral:7b, llama3.1:8b, gemma3:12b

Лог: logs/02_ollama_HHMMSS.log
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from browser_use import ChatOllama
from browser_use.agent.service import Agent
from browser_use.browser.profile import BrowserProfile
from log_utils import setup_logging, make_step_callback, save_run_summary

TASK = (
    "Go to https://coinmarketcap.com/currencies/bitcoin/ "
    "and return the current BTC price in USD. "
    "Just navigate there and extract the price number, nothing else."
)

# Попробуй разные модели — закомментируй ненужные:
MODELS_TO_TRY = [
    "qwen3.5:4b",
    # "gemma3:4b",
]


async def try_model(model_name: str, log) -> bool:
    """Запускает агента с указанной моделью. Возвращает True если успех."""
    log.info(f"── Модель: {model_name} ──")

    llm = ChatOllama(model=model_name)

    profile = BrowserProfile(
        headless=False,
        wait_for_network_idle_page_load_time=2.0,
    )

    agent = Agent(
        task=TASK,
        llm=llm,
        browser_profile=profile,
        use_vision=True,
        # flash_mode=True: упрощённый JSON-формат специально для слабых моделей
        # автоматически ставит enable_planning=False и use_thinking=False
        flash_mode=True,
        use_judge=False,
        max_failures=2,
        register_new_step_callback=make_step_callback(log),
    )

    result = await agent.run(max_steps=8)
    save_run_summary(log, result, TASK)
    return result.is_done() and bool(result.final_result())


async def main():
    log = setup_logging("02_ollama")
    log.info(f"Задача: {TASK}")
    log.info("")
    log.info("Локальные модели для browser-use требуют минимум 7B+.")
    log.info("flash_mode=True используется для слабых моделей (упрощённый JSON).")
    log.info("")

    for model in MODELS_TO_TRY:
        success = await try_model(model, log)
        log.info(f"Результат {model}: {'✓ OK' if success else '✗ не справилась'}")
        log.info("")


if __name__ == "__main__":
    asyncio.run(main())

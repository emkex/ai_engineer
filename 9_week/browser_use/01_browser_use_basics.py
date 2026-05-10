"""
browser-use 0.12.x: минимальный пример с Claude Haiku.

Цикл работы агента:
  DOM-snapshot → LLM решает → action → новый DOM → ...

Почему use_thinking=False для Haiku:
  По умолчанию use_thinking=True — browser-use ожидает extended thinking блоки.
  Haiku их не возвращает корректно → action field missing → падение.
  Sonnet/Opus — работают с thinking. Haiku — нужен use_thinking=False.

Лог: logs/01_basics_HHMMSS.log — краткий, читаемый.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from browser_use import ChatAnthropic
from browser_use.agent.service import Agent
from browser_use.browser.profile import BrowserProfile
from log_utils import setup_logging, make_step_callback, save_run_summary

load_dotenv()

TASK = (
    "Go to https://finance.yahoo.com/ "
    "and return the current stock price AAPL and day change percentage."
)


async def main():
    log = setup_logging("01_basics")
    log.info(f"Модель: claude-haiku-4-5-20251001")
    log.info(f"Задача: {TASK}")

    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

    profile = BrowserProfile(
        headless=False,
        highlight_elements=True,
        wait_for_network_idle_page_load_time=3.0,
    )

    agent = Agent(
        task=TASK,
        llm=llm,
        browser_profile=profile,
        use_vision=True,
        generate_gif=False,
        use_thinking=False,     # Haiku не поддерживает extended thinking
        enable_planning=False,
        use_judge=False,        # отключаем судью — он требует скриншот финальной страницы
        register_new_step_callback=make_step_callback(log),
    )

    result = await agent.run(max_steps=12)
    save_run_summary(log, result, TASK)


if __name__ == "__main__":
    asyncio.run(main())

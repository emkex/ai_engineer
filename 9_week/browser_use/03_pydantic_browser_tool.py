"""
PydanticAI агент с браузером как ИНСТРУМЕНТОМ.

Ключевое отличие от browser-use подхода:
- browser-use: весь агент = браузерный навигатор
- этот подход: общий агент, браузер — один инструмент из многих

Когда нужно: агент делает разные вещи (читает файлы, считает, ходит в браузер).

Playwright используется напрямую — он уже установлен вместе с browser-use.
Лог: logs/03_pydantic_HHMMSS.log
"""
import asyncio
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from pydantic_ai import Agent
from playwright.async_api import async_playwright
from log_utils import setup_logging

load_dotenv()

# Заглушить шум playwright/httpx
for _lib in ("playwright", "httpx", "httpcore"):
    logging.getLogger(_lib).setLevel(logging.WARNING)

agent = Agent(
    "anthropic:claude-haiku-4-5-20251001",
    system_prompt=(
        "You are a financial analyst. "
        "Use fetch_page_text to get real-time data from websites. "
        "Be concise."
    ),
)


@agent.tool_plain
async def fetch_page_text(url: str) -> str:
    """Открывает URL headless-браузером, возвращает текст страницы (до 4000 символов)."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            text = await page.inner_text("body")
        except Exception as e:
            text = f"Page load error: {e}"
        finally:
            await browser.close()
    return text[:4000]


async def main():
    log = setup_logging("03_pydantic")

    questions = [
        # Прямой URL — надёжнее чем поиск
        "Fetch https://finance.yahoo.com/quote/AAPL and return current price and last news",
        "Fetch https://coinmarketcap.com/currencies/ethereum/ and return ETH price in USD and general sentiment.",
    ]

    for question in questions:
        log.info(f"Вопрос: {question}")
        try:
            result = await agent.run(question)
            log.info(f"Ответ:  {result.output[:300]}")
        except Exception as e:
            log.error(f"Ошибка: {e}")
        log.info("─" * 50)


if __name__ == "__main__":
    asyncio.run(main())

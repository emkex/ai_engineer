"""
browser-use + Pydantic: детерминированный структурированный вывод.

Как это работает:
1. Определяешь Pydantic-модель с нужными полями
2. Передаёшь её в Agent(output_model_schema=YourModel)
3. browser-use автоматически:
   - добавляет JSON-схему в системный промпт (агент знает ЧТО вернуть)
   - парсит ответ агента в твою модель
4. result.get_structured_output(YourModel) → типизированный объект

Никакого PydanticAI здесь не нужно — browser-use поддерживает это нативно.
PydanticAI нужен когда браузер = один из многих инструментов агента (см. 03_).

Лог: logs/06_structured_HHMMSS.log
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from browser_use import ChatAnthropic
from browser_use.agent.service import Agent
from browser_use.browser.profile import BrowserProfile
from log_utils import setup_logging, make_step_callback

load_dotenv()

BROWSER_UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0'
BROWSER_HEADERS: dict[str, str] = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}
ALLOWED_DOMAINS = [
    "*.yahoo.com",
    "yahoo.com",
    "*.oath.com",
    "coinmarketcap.com",
]


class HeaderAgent(Agent):
    """Agent с инъекцией HTTP-заголовков через CDP при первом шаге."""

    def __init__(self, *args, extra_headers: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._extra_headers = extra_headers or {}
        self._headers_injected = False

    async def _execute_actions(self) -> None:
        if self._extra_headers and not self._headers_injected:
            try:
                await self.browser_session.set_extra_headers(self._extra_headers)
                self._headers_injected = True
            except Exception:
                pass
        await super()._execute_actions()



# ── Схема вывода ──────────────────────────────────────────────────────────────

class StockSnapshot(BaseModel):
    """Текущий снапшот акции — агент обязан заполнить все поля."""
    ticker: str             = Field(description="Stock ticker, e.g. AAPL")
    price: float            = Field(description="Current price in USD")
    change_abs: float       = Field(description="Absolute day change, e.g. +5.90")
    change_pct: float       = Field(description="Day change percentage, e.g. +2.05")
    exchange: Optional[str] = Field(None, description="Exchange name, e.g. NasdaqGS")
    as_of: Optional[str]    = Field(None, description="Timestamp of the price")


class CryptoSnapshot(BaseModel):
    """Снапшот криптовалюты."""
    symbol: str          = Field(description="Crypto symbol, e.g. BTC")
    price_usd: float     = Field(description="Current price in USD")
    change_24h_pct: float = Field(description="24h change percentage")
    market_cap_b: Optional[float] = Field(None, description="Market cap in billions USD")


# ── Вспомогательная функция ──────────────────────────────────────────────────

async def fetch_structured(task: str, schema: type, log, max_steps: int = 25):
    """Запускает агента и возвращает типизированный объект схемы."""
    agent = HeaderAgent(
        task=task,
        llm=ChatAnthropic(model="claude-haiku-4-5-20251001"),
        browser_profile=BrowserProfile(
            headless=False,
            wait_for_network_idle_page_load_time=3.0,
            user_agent=BROWSER_UA,
            allowed_domains=ALLOWED_DOMAINS,
        ),
        output_model_schema=schema,   # ← ключевой параметр
        use_thinking=False,
        enable_planning=False,
        use_judge=False,
        use_vision=True,
        register_new_step_callback=make_step_callback(log),
        extra_headers=BROWSER_HEADERS,
    )

    result = await agent.run(max_steps=max_steps)

    # Получаем типизированный объект — None если агент не смог
    structured = result.get_structured_output(schema)
    return structured


# ── Демо ─────────────────────────────────────────────────────────────────────

async def main():
    log = setup_logging("06_structured")

    # --- Пример 1: Акция AAPL ---
    log.info("── Пример 1: StockSnapshot (AAPL) ──")
    stock = await fetch_structured(
        task=(
            "Go to https://finance.yahoo.com/ (main page). "
            "If you see a cookie consent popup, click 'Accept all' or 'Agree' to dismiss it. "
            "Then search for AAPL and extract: "
            "ticker, current price, absolute day change, day change %, "
            "exchange name, and price timestamp."
        ),
        schema=StockSnapshot,
        log=log,
    )

    if stock:
        log.info(f"  ticker      : {stock.ticker}")
        log.info(f"  price       : ${stock.price:.2f}")
        log.info(f"  change      : {stock.change_abs:+.2f}  ({stock.change_pct:+.2f}%)")
        log.info(f"  exchange    : {stock.exchange}")
        log.info(f"  as_of       : {stock.as_of}")
        # Пример использования как объект — не строка!
        if stock.change_pct > 0:
            log.info(f"  → СИГНАЛ: акция растёт +{stock.change_pct:.2f}% за день")
    else:
        log.warning("  Структурированный вывод не получен")

    log.info("")

    # --- Пример 2: Крипта BTC ---
    log.info("── Пример 2: CryptoSnapshot (BTC) ──")
    crypto = await fetch_structured(
        task=(
            "Go to https://coinmarketcap.com/currencies/bitcoin/ and extract: "
            "symbol, current price in USD, 24h change percentage, market cap."
        ),
        schema=CryptoSnapshot,
        log=log,
    )

    if crypto:
        log.info(f"  symbol      : {crypto.symbol}")
        log.info(f"  price_usd   : ${crypto.price_usd:,.2f}")
        log.info(f"  24h change  : {crypto.change_24h_pct:+.2f}%")
        log.info(f"  market_cap  : ${crypto.market_cap_b:.1f}B" if crypto.market_cap_b else "  market_cap  : N/A")
        # Использование как объект
        alert = "📈 РОСТ" if crypto.change_24h_pct > 2 else "📉 ПАДЕНИЕ" if crypto.change_24h_pct < -2 else "→ боковик"
        log.info(f"  → {alert}")
    else:
        log.warning("  Структурированный вывод не получен")


if __name__ == "__main__":
    asyncio.run(main())

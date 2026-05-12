"""
Production-ready агент с браузером.

Архитектура:
- Секреты: env_file в docker-compose, НЕ хардкодятся в образе
- Прокси: браузер читает HTTPS_PROXY из окружения
- Filesystem: bind-mount только /workspace, остальное read-only
- Модель: Haiku (облако) или llama3.2 (Ollama на хосте/контейнере)

Запуск локально (тест без Docker):
    python 05_production/agent.py

Запуск в Docker:
    docker-compose up --build

Лог: logs/production_HHMMSS.log (внутри /workspace в Docker)
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from browser_use.agent.service import Agent
from browser_use.browser.profile import BrowserProfile
from log_utils import setup_logging, make_step_callback, save_run_summary

# Секреты с хоста: docker-compose передаёт через env_file, не внутри образа
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

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


def build_llm():
    """Выбирает модель: облако или Ollama."""
    use_local = os.environ.get("USE_LOCAL_MODEL", "false").lower() == "true"

    if use_local:
        from browser_use import ChatOllama
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return ChatOllama(model="llama3.2", ollama_base_url=host, temperature=0, num_ctx=8192)
    else:
        from browser_use import ChatAnthropic
        return ChatAnthropic(model="claude-haiku-4-5-20251001")


def build_browser_profile() -> BrowserProfile:
    """BrowserProfile с прокси из окружения."""
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    proxy_config = None

    if proxy_url:
        proxy_config = {"server": proxy_url}
        user = os.environ.get("PROXY_USER")
        pwd = os.environ.get("PROXY_PASS")
        if user and pwd:
            proxy_config.update({"username": user, "password": pwd})

    return BrowserProfile(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",           # нет дисплея — GPU pipeline не нужен
            "--no-zygote",             # без zygote-процесса (лучше в Docker)
            "--no-first-run",
        ],
        proxy=proxy_config,
        wait_for_network_idle_page_load_time=5.0,  # coinmarketcap — тяжёлый SPA
        user_agent=BROWSER_UA,
        allowed_domains=ALLOWED_DOMAINS,
    )


async def run_monitor(task: str) -> None:
    log = setup_logging("production")
    llm = build_llm()

    model_info = "ollama:llama3.2" if os.environ.get("USE_LOCAL_MODEL") == "true" else "haiku"
    log.info(f"Модель: {model_info}")
    log.info(f"Задача: {task}")

    if os.environ.get("HTTPS_PROXY"):
        log.info(f"Прокси:  {os.environ['HTTPS_PROXY']}")

    agent = HeaderAgent(
        task=task,
        llm=llm,
        browser_profile=build_browser_profile(),
        use_vision=False,       # экономим токены в продакшне
        use_thinking=False,
        enable_planning=False,
        use_judge=False,
        register_new_step_callback=make_step_callback(log),
        extra_headers=BROWSER_HEADERS,
    )

    result = await agent.run(max_steps=20)
    save_run_summary(log, result, task)

    # Здесь можно добавить: notify_telegram(result) / write_to_db(result)


async def main():
    task = os.environ.get(
        "AGENT_TASK",
        "Go to https://coinmarketcap.com/currencies/bitcoin/ and return BTC price in USD.",
    )
    await run_monitor(task)


if __name__ == "__main__":
    asyncio.run(main())

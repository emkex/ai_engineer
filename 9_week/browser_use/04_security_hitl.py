"""
Безопасность и Human-in-the-Loop для browser-use агента.

Топ-5 рисков:
1. Prompt injection  — вредный текст на странице выполняется как инструкция
2. Confused deputy   — агент с правами пользователя делает что хочет атакующий
3. Data exfiltration — агент читает ~/.ssh и отправляет на внешний сервер
4. Destructive actions — rm -rf, удаление аккаунта
5. Approval fatigue  — пользователь жмёт OK не читая

Решения:
1. BrowserProfile.allowed_domains — нативный domain allowlist в v0.12.x
2. Action risk classifier + HITL — dangerous actions require y/N confirmation
3. max_steps limit — ограничение цикла
4. Docker read-only bind-mount — только /workspace доступен агенту
5. Structured approval — показывает ЧТО именно, не просто "OK?"

Запуск:
  python 04_security_hitl.py manual   — без API ключа, симуляция HITL
  python 04_security_hitl.py          — реальный агент (нужен ANTHROPIC_API_KEY)

Лог: logs/04_security_HHMMSS.log
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from browser_use import ChatAnthropic
from browser_use.agent.service import Agent
from browser_use.browser.profile import BrowserProfile
from log_utils import setup_logging, make_step_callback, save_run_summary

load_dotenv()

# Заголовки под реальный Firefox — помогают пройти bot-detection Yahoo.
# Accept-Encoding убран: Playwright управляет сжатием автоматически.
BROWSER_HEADERS: dict[str, str] = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}
BROWSER_UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0'

# Слой 1: Allowlist доменов — агент не выйдет за пределы.
# List (не set) нужен для fnmatch-паттернов — *.yahoo.com ловит все субдомены:
# finance.yahoo.com, consent.yahoo.com, login.yahoo.com и т.д.
ALLOWED_DOMAINS = [
    "*.yahoo.com",       # все субдомены Yahoo (включая consent.yahoo.com)
    "yahoo.com",
    "*.oath.com",        # GDPR consent: guce.oath.com
    "coinmarketcap.com",
    "investing.com",
]

# Слой 2: Классификация действий по уровню риска.
# click → "high" намеренно для демо HITL: каждый клик требует y/N.
# В продакшне обычно "medium" (авто-одобрен) или контекстная проверка по деталям.
ACTION_RISK: dict[str, str] = {
    "navigate": "low",
    "scroll": "low",
    "extract_content": "low",
    "screenshot": "low",
    "click": "medium",       
    "input": "high",       # ← DEMO: поднято с medium чтобы увидеть y/N в терминале
    "select_option": "medium",
    "submit_form": "high",
    "upload_file": "high",
    "download_file": "high",
    "execute_shell": "critical",
    "send_message": "critical",
    "delete": "critical",
    "purchase": "critical",
}


def classify_action(action_name: str) -> str:
    action_lower = action_name.lower()
    for action, risk in ACTION_RISK.items():
        if action in action_lower:
            return risk
    return "medium"


async def human_approval(action_name: str, details: str, risk: str) -> bool:
    """Паттерн structured approval — показывает ЧТО, не просто "OK?"."""
    colors = {
        "low": "", "medium": "\033[33m",
        "high": "\033[31m", "critical": "\033[1;31m",
    }
    color = colors.get(risk, "")
    reset = "\033[0m"

    if risk == "low":
        return True

    print(f"\n{color}[{risk.upper()}] {action_name}{reset}  —  {details}")

    if risk == "medium":
        print("  → auto-approved (medium)")
        return True

    return input("  Разрешить? [y/N]: ").strip().lower() == "y"


class HitlAgent(Agent):
    """
    Agent с реальным HITL: переопределяет _execute_actions(),
    которая вызывается ПОСЛЕ того как LLM решил что делать, но ДО выполнения.
    Порядок в шаге: _get_next_action → _execute_actions → _post_process.
    """

    def __init__(self, *args, log, extra_headers: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = log
        self._extra_headers = extra_headers or {}
        self._headers_injected = False

    async def _execute_actions(self) -> None:
        # Инжектируем заголовки один раз — сразу после инициализации браузера.
        if self._extra_headers and not self._headers_injected:
            try:
                await self.browser_session.set_extra_headers(self._extra_headers)
                self._headers_injected = True
                self._log.info("  ✓ HTTP-заголовки установлены через CDP")
            except Exception as e:
                self._log.warning(f"  ⚠ Заголовки не установлены: {e}")

        if self.state.last_model_output is None:
            return
        for action in self.state.last_model_output.action:
            # action — Pydantic-дискриминатор ActionModel, реальный тип внутри .root
            root = getattr(action, "root", action)
            action_name = root.__class__.__name__
            risk = classify_action(action_name)
            details = str(root)[:100]
            approved = await human_approval(action_name, details, risk)
            if not approved:
                self._log.warning(f"  ✗ СТОП: '{action_name}' отклонено — агент остановлен")
                self.state.stopped = True
                return
        await super()._execute_actions()


class SafeAgent:
    """
    4 слоя изоляции:
      1. BrowserProfile.allowed_domains  (этот файл)
      2. HitlAgent._execute_actions — реальная блокировка ДО выполнения
      3. max_steps                        (этот файл)
      4. Docker read-only FS             (05_production/docker-compose.yml)
    """

    def __init__(self, task: str, llm, profile: BrowserProfile, log):
        self.task = task
        self.llm = llm
        self.profile = profile
        self.log = log

    async def run(self, max_steps: int = 20):
        agent = HitlAgent(
            task=self.task,
            llm=self.llm,
            browser_profile=self.profile,
            use_vision=True,
            use_thinking=False,
            enable_planning=False,
            use_judge=False,
            register_new_step_callback=make_step_callback(self.log),
            log=self.log,
            extra_headers=BROWSER_HEADERS,
        )
        result = await agent.run(max_steps=max_steps)
        save_run_summary(self.log, result, self.task)
        return result


async def demo_hitl():
    """Реальный агент с domain allowlist и кратким логом."""
    log = setup_logging("04_security")

    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

    # allowed_domains — list с fnmatch-паттернами (*.yahoo.com ловит все субдомены).
    # Блокирует только действия АГЕНТА — ручной ввод URL в браузере не перехватывается.
    profile = BrowserProfile(
        headless=False,
        wait_for_network_idle_page_load_time=3.0,
        save_conversation_path="./conversation_log.json",
        allowed_domains=ALLOWED_DOMAINS,
        user_agent=BROWSER_UA,
    )

    # Идём на главную страницу, как в 01 — там попап проще и cookie flow стандартный.
    # Прямой /quote/AAPL вызывает тяжёлый consent redirect через guce.oath.com.
    task = (
        "Go to https://finance.yahoo.com/ — the main page, not the quote page directly. "
        "If you see a cookie consent popup or privacy notice, click 'Accept all' or 'Agree' to dismiss it. "
        "Then find the AAPL stock quote (use the search bar if needed) "
        "and return the current AAPL price and 24h change %. And follow (action approved)."
    )

    log.info(f"Allowed domains: {', '.join(ALLOWED_DOMAINS)}")
    log.info(f"Задача: {task}")

    safe = SafeAgent(task=task, llm=llm, profile=profile, log=log)
    await safe.run(max_steps=25)


if __name__ == "__main__":
    asyncio.run(demo_hitl())

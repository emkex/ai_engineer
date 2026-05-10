"""
Утилиты логирования для browser-use скриптов.

Использование:
    from log_utils import setup_logging, make_step_callback, save_run_summary

    log = setup_logging("01_basics")   # создаёт logs/01_basics_YYYYMMDD_HHMMSS.log
    agent = Agent(..., register_new_step_callback=make_step_callback(log))
    result = await agent.run(...)
    save_run_summary(log, result, task)
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(script_name: str) -> logging.Logger:
    """
    Подавляет INFO-спам browser_use, пишет краткий лог в файл + консоль.
    Возвращает логгер для нашего кода.
    """
    # Заглушить все шумные библиотеки
    for noisy in ("browser_use", "bubus", "cdp_use", "playwright", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Папка для логов рядом со скриптами
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"{script_name}_{ts}.log"

    # Наш логгер — пишет и в файл, и в консоль
    logger = logging.getLogger(f"run.{script_name}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info(f"=== Лог: {log_path.name} ===")
    return logger


def make_step_callback(logger: logging.Logger):
    """
    Возвращает callback для register_new_step_callback.
    Печатает одну строку на шаг: номер, реальный тип action, цель.
    """
    def callback(state, output, step_num: int):
        try:
            if output.action:
                # action — Pydantic-дискриминатор ActionModel, реальный тип в .root
                raw = output.action[0]
                root = getattr(raw, "root", raw)
                action_type = root.__class__.__name__
            else:
                action_type = "—"
            goal = (output.current_state.next_goal or "")[:80]
            logger.info(f"  Шаг {step_num:02d}  [{action_type}]  {goal}")
        except Exception:
            logger.info(f"  Шаг {step_num:02d}")
    return callback


def save_run_summary(logger: logging.Logger, result, task: str) -> None:
    """Логирует итог запуска: статус, результат, список actions."""
    logger.info("─" * 60)
    logger.info(f"Задача: {task}")
    logger.info(f"Успех:  {result.is_done()}")
    logger.info(f"Шагов:  {len(result.action_names())}")
    logger.info(f"Actions: {' → '.join(result.action_names())}")
    logger.info("─" * 60)
    final = result.final_result()
    if final:
        for line in final.splitlines():
            logger.info(f"  {line}")
    else:
        logger.info("  (нет результата)")
    logger.info("─" * 60)

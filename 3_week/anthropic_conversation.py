import os
from dotenv import load_dotenv
from anthropic import Anthropic

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CUR_DIR, '.env'))

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# =============================================================================
# 1. РАЗБОР RESPONSE — что возвращает API
# =============================================================================

def show_response(message):
    """Показывает все поля ответа от API."""
    print("\n── RESPONSE ─────────────────────────────────")
    print(f"  id            : {message.id}")
    print(f"  model         : {message.model}")
    print(f"  stop_reason   : {message.stop_reason}")   # end_turn / max_tokens / stop_sequence
    print(f"  stop_sequence : {message.stop_sequence}") # None если stop_reason = end_turn

    print("\n  [usage — токены]")
    print(f"  input_tokens  : {message.usage.input_tokens}")   # сколько токенов в твоём запросе
    print(f"  output_tokens : {message.usage.output_tokens}")  # сколько потратил на ответ

    print("\n  [content — тело ответа]")
    for block in message.content:
        print(f"  type: {block.type}")
        print(f"  text: {block.text[:200]}")
    print("─────────────────────────────────────────────")


# =============================================================================
# 2. МНОГОХОДОВОЙ ДИАЛОГ — история передаётся вперёд
#
# Ключевая идея: messages — это список, куда мы сами дописываем
# и ответ ассистента, и следующий вопрос пользователя.
# Claude не помнит ничего сам — каждый раз получает всю историю заново.
# =============================================================================

def run_conversation():
    history = []  # список {"role": ..., "content": ...}

    # Четыре хода диалога — одна тема, каждый вопрос строится на предыдущем
    turns = [
        "Насколько большая разница в температуре между Ереваном и горами в Армении?",
        "Как назвать дочь с отчеством Евгеньевна?"
    ]

    for i, user_text in enumerate(turns, 1):
        # Добавляем вопрос пользователя в историю
        history.append({"role": "user", "content": user_text})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="Основываешься на фактах, не угождаешь и не фантазируешь.",
            messages=history,   # вся история целиком при каждом вызове
            temperature=0.7,    # низкая — факты, не фантазии
        )

        assistant_text = response.content[0].text

        # Дописываем ответ ассистента в историю — он станет контекстом для следующего хода
        history.append({"role": "assistant", "content": assistant_text})

        print(f"\n── ХОД {i} ───────────────────────────────────")
        print(f"  USER      : {user_text}")
        print(f"  ASSISTANT : {assistant_text}")
        print(f"  tokens    : in={response.usage.input_tokens} out={response.usage.output_tokens}")

    print(f"\n  Итого сообщений в истории: {len(history)}")  # 8 = 4 user + 4 assistant
    return history


# =============================================================================
# 3. ИНТЕРЕСНЫЕ ПАРАМЕТРЫ
#
# temperature  — случайность ответа. 0.0 = детерминировано, 1.0 = творчески
# top_p        — альтернатива temperature (nucleus sampling). Обычно либо одно либо другое
# max_tokens   — жёсткий потолок длины ответа (stop_reason станет "max_tokens")
# stop_sequences — список строк, на которых Claude остановится сам
# system       — системный промпт (инструкция, роль, формат)
# =============================================================================

def show_stop_sequence():
    """stop_sequences — Claude остановится когда встретит эту строку в своём ответе."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": "Перечисли активы: акции, облигации, ETF, золото, уголь, СПГ, недвижимость."}],
        stop_sequences=["ETF"],  # остановится перед третьим пунктом
    )
    print("\n── STOP SEQUENCE ────────────────────────────")
    print(f"  stop_reason   : {response.stop_reason}")    # будет "stop_sequence"
    print(f"  stop_sequence : {response.stop_sequence}")  # "ETF"
    print(f"  ответ         : {response.content[0].text}")
    print("─────────────────────────────────────────────")


def show_temperature():
    """temperature=0.0 vs temperature=1.0 — один и тот же вопрос, разные ответы."""
    question = "Назови один актив для защиты от инфляции."

    for temp in [0.0, 1.0]:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{"role": "user", "content": question}],
            temperature=temp,
        )
        print(f"\n── temperature={temp} ───────────────────────")
        print(f"  {response.content[0].text.strip()}")


# =============================================================================
# ЗАПУСК
# =============================================================================

if __name__ == '__main__':
    # # 1. Разбор ответа
    # print("══ 1. РАЗБОР RESPONSE ══════════════════════")
    # r = client.messages.create(
    #     model="claude-haiku-4-5-20251001",
    #     max_tokens=100,
    #     messages=[{"role": "user", "content": "Что такое черемша? Одно предложение."}],
    # )
    # show_response(r)

    # 2. Многоходовой диалог
    print("\n══ 2. ДИАЛОГ 4 ХОДА ════════════════════════")
    run_conversation()

    # # 3. stop_sequences
    # print("\n══ 3. STOP SEQUENCE ════════════════════════")
    # show_stop_sequence()

    # # 4. temperature
    # print("\n══ 4. TEMPERATURE 0.0 vs 1.0 ══════════════")
    # show_temperature()

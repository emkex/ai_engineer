import os
from dotenv import load_dotenv
from anthropic import Anthropic

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CUR_DIR, '.env'))


client = Anthropic(
    # This is the default and can be omitted
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

method_api = '''
(method) def create(
    *,
    max_tokens: int,
    messages: Iterable[MessageParam],
    model: ModelParam,
    cache_control: CacheControlEphemeralParam | Omit | None = omit,
    container: str | Omit | None = omit,
    inference_geo: str | Omit | None = omit,
    metadata: MetadataParam | Omit = omit,
    output_config: OutputConfigParam | Omit = omit,
    service_tier: Omit | Literal['auto', 'standard_only'] = omit,
    stop_sequences: SequenceNotStr[str] | Omit = omit,
    stream: Omit | Literal[False] = omit,
    system: str | Iterable[TextBlockParam] | Omit = omit,
    temperature: float | Omit = omit,
    thinking: ThinkingConfigParam | Omit = omit,
    tool_choice: ToolChoiceParam | Omit = omit,
    tools: Iterable[ToolUnionParam] | Omit = omit,
    top_k: int | Omit = omit,
    top_p: float | Omit = omit,
    extra_headers: Headers | None = None,
    extra_query: Query | None = None,
    extra_body: Body | None = None,
    timeout: float | Timeout | NotGiven | None = not_given
) -> Message
'''

with client.messages.stream(
    max_tokens=2048,
    system='ты учишь меня работать с Anthropic models через API',
    messages=[
        {
            "role": "user",
            "content": "опиши, какой ответ я получаю обычно от message = client.messages.create(). Json? что там есть?",
        }
    ],
    temperature=0.5,
    model="claude-haiku-4-5",
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()  # перенос строки после завершения
    message = stream.get_final_message()

print(message.usage) # tokens spent

# [TextBlock(citations=None, text='# Параметры метода `create` для Anthropic API\n\n## 🔴 Обязательные параметры\n\n| Параметр | Тип | Описание |\n|----------|-----|----------|\n| `max_tokens` | `int` | Максимальное количество токенов в ответе. Например `1024`, `4096` |\n| `messages` | `Iterable[MessageParam]` | История диалога — список сообщений `[{"role": "user", "content": "..."}]` |\n| `model` | `ModelParam` | Какую модель использовать. Например `"claude-opus-4-5"` |\n\n---\n\n## 🟡 Основные опциональные параметры\n\n| Параметр | Тип | Описание |\n|----------|-----|----------|\n| `system` | `str \\| Iterable[TextBlockParam]` | Системный промпт — инструкции для модели перед диалогом |\n| `temperature` | `float` | Случайность ответов. `0.0` — детерминировано, `1.0` — креативно |\n| `top_p` | `float` | Nucleus sampling. Альтернатива temperature. Обычно `0.0–1.0` |\n| `top_k` | `int` | Ограничивает выбор следующего токена top-K вариантами |\n| `stop_sequences` | `list[str]` | Строки, при появлении которых модель останавливается |\n| `stream` | `Literal[False]` | Стриминг ответа. Здесь явно `False` — без стриминга |\n\n---\n\n## 🔵 Инструменты и структурированный вывод\n\n| Параметр | Тип | Описание |\n|----------|-----|----------|\n| `tools` | `Iterable[ToolUnionParam]` | Список инструментов (функций), которые модель может вызывать |\n| `tool_choice` | `ToolChoiceParam` | Управляет выбором инструмента: `auto`, `any`, `tool` |\n| `output_config` | `OutputConfigParam` | Настройки структурированного вывода |\n\n---\n\n## 🟣 Мышление (Extended Thinking)\n\n| Параметр | Тип | Описание |\n|----------|-----|----------|\n| `thinking` | `ThinkingConfigParam` | Включает режим "размышления" модели перед ответом. `{"type": "enabled", "budget_tokens": 5000}` |\n\n---\n\n## ⚙️ Инфраструктурные параметры\n\n| Параметр | Тип | Описание |\n|----------|-----|----------|\n| `metadata` | `MetadataParam` | Метаданные запроса, например `user_id` для трекинга |\n| `cache_control` | `CacheControlEphemeralParam` | Управление кешированием промптов (Prompt Caching) |\n| `service_tier` | `\'auto\' \\| \'standard_only\'` | Уровень сервиса: `auto` — приоритетный, `standard_only` — стандартный |\n| `container` | `str` | ID контейнера (для Files API / sandbox) |\n| `inference_geo` | `str` | Географический регион для инференса |\n\n---\n\n## 🔧 Низкоуровневые HTTP параметры\n\n| Параметр | Тип | Описание |\n|----------|-----|----------|\n| `extra_headers` | `Headers` | Дополнительные HTTP заголовки |\n| `extra_query` | `Query` | Дополнительные query-параметры |\n| `extra_body` | `Body` | Дополнительные поля в тело запроса |\n| `timeout` | `float \\| Timeout` | Таймаут запроса в секундах |\n\n---\n\n## 💡 Важные взаимосвязи\n\n```\ntemperature ←→ top_p  # Не рекомендуется менять оба одновременно\nthinking             # При включении требует увеличенного max_tokens (мин. ~16000)\ntools + tool_choice  # Работают в паре\n```\n\nС чего хочешь начать?', type='text')]
print(message.content[0].text)
# headers of response
# print(message.response_headers)
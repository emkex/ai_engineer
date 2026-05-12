# Docker-система проекта browser_use/05_production

Подробный разбор каждого файла, каждой строки, и того что происходит во время выполнения.

---

## 1. Карта проекта

```
browser_use/
│
├── log_utils.py              ← утилиты логирования: setup_logging, make_step_callback,
│                                save_run_summary. Создаёт папку logs/ рядом с собой
├── .env                      ← секреты хоста: ANTHROPIC_API_KEY, куки FT.com,
│                                AGENT_TASK, USE_LOCAL_MODEL, OLLAMA_HOST. НЕ коммитится.
│
├── 01_browser_use_basics.py  ← упражнение 1: базовый агент
├── 02_with_ollama.py         ← упражнение 2: локальная модель
├── 03_pydantic_browser_tool.py
├── 04_security_hitl.py
├── 06_structured_output.py
│
└── 05_production/
    ├── Dockerfile            ← инструкция сборки образа: ОС + зависимости + код
    ├── docker-compose.yml    ← оркестратор: что запускать, с какими env/volumes/сетями
    ├── agent.py              ← production-агент: выбор модели, прокси, ограничение доменов
    ├── log_utils.py          ← дубликат ../log_utils.py (исторически — сейчас лишний,
    │                            Dockerfile копирует версию из browser_use/)
    ├── requirements.txt      ← зависимости Python для контейнера
    └── workspace/            ← bind-mount с хостом: логи и результаты работы агента
```

---

## 2. Dockerfile — шаг за шагом

Текущий Dockerfile:

```dockerfile
FROM python:3.12-slim

RUN apt-get update -qq && apt-get install -y -qq \
    curl wget gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY 05_production/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN playwright install chromium --with-deps

WORKDIR /workspace

COPY 05_production/agent.py /app/agent.py
COPY log_utils.py /app/log_utils.py

RUN useradd -m -u 1000 agent
USER agent

CMD ["python", "/app/agent.py"]
```

### `FROM python:3.12-slim`

**Что делает:** берёт готовый образ с Docker Hub. Это "фотография" файловой системы Debian Linux с уже установленным Python 3.12.

**Что такое slim:** существуют варианты образа — `python:3.12` (полный, ~900 MB), `python:3.12-slim` (~130 MB), `python:3.12-alpine` (~50 MB). Slim отличается тем, что убраны пакеты для разработки и документация, но оставлено всё что нужно для запуска Python-программ. Alpine — ещё меньше, но несовместим с частью pip-пакетов из-за другого libc.

**Без этой строки:** нечего собирать, `FROM` обязателен в любом Dockerfile.

### `RUN apt-get update -qq && apt-get install -y -qq curl wget gnupg && rm -rf /var/lib/apt/lists/*`

**Что делает:** обновляет список пакетов Debian и устанавливает `curl`, `wget`, `gnupg`. Флаг `-qq` подавляет вывод. `rm -rf /var/lib/apt/lists/*` удаляет кеш списков пакетов.

**Зачем именно здесь:** Playwright при установке Chromium (`playwright install chromium --with-deps`) вызывает системный менеджер пакетов и ему нужны curl/wget для загрузки бинарников. gnupg нужен для проверки подписей.

**Зачем `rm -rf /var/lib/apt/lists/*`:** каждая строка `RUN` создаёт слой образа. Если не удалить кеш apt — он войдёт в слой и образ будет тяжелее на ~30–50 MB. Удаление в том же `RUN` гарантирует что кеш не попадёт в слой.

**Без этой строки:** `playwright install chromium --with-deps` упадёт с ошибкой "unable to install chromium dependencies".

### `COPY 05_production/requirements.txt /tmp/requirements.txt`

**Что делает:** копирует файл с хоста (из build context) в контейнер по пути `/tmp/requirements.txt`.

**Почему `05_production/requirements.txt`:** build context задан как `..` (папка `browser_use/`), поэтому пути в COPY — относительно `browser_use/`. Файл `browser_use/05_production/requirements.txt` → `/tmp/requirements.txt`.

**Почему сначала requirements, потом код:** слои Docker кешируются. Если сначала скопировать код (он меняется часто), а потом requirements — при каждом изменении кода будет пересобираться и `pip install`. Порядок: сначала то что меняется редко (зависимости), потом то что меняется часто (код). Тогда `pip install` не будет переустанавливаться при каждом `docker-compose up --build`.

### `RUN pip install --no-cache-dir -r /tmp/requirements.txt`

**Что делает:** устанавливает Python-пакеты из requirements.txt.

**`--no-cache-dir`:** pip кеширует скачанные wheel-файлы. В контейнере этот кеш после установки бесполезен, только занимает место. Флаг говорит: не сохранять.

**Без этой строки:** `from browser_use import Agent` упадёт с ImportError.

### `RUN playwright install chromium --with-deps`

**Что делает:** скачивает и устанавливает Chromium нужной версии (Playwright управляет версией сам, независимо от системного браузера). `--with-deps` дополнительно устанавливает все системные библиотеки которые нужны Chromium (libglib, libnss, libatk и ещё ~30 зависимостей).

**Почему не использовать системный Chromium:** Playwright требует точно определённую версию, потому что его CDP-протокол зависит от конкретного API браузера. Системный `/usr/bin/chromium` может быть другой версии и сломать автоматизацию.

**Это самый долгий шаг сборки:** ~400 MB, занимает 2–5 минут. Но он кешируется — при изменении только `agent.py` этот слой не пересобирается.

### `WORKDIR /workspace`

**Что делает:** устанавливает "текущую директорию" контейнера. Все последующие команды в Dockerfile, а также CMD при старте контейнера будут выполняться из `/workspace`.

**Важно:** `WORKDIR` также создаёт директорию если её нет. На этом шаге `/workspace` принадлежит `root` (мы ещё не переключили пользователя). Это важно для bind-mount: если Docker монтирует `./workspace:/workspace:rw`, то директория уже существует.

**Что это меняет для агента:** текущая папка процесса будет `/workspace`. Если бы код писал `open("output.txt", "w")`, файл появился бы в `/workspace/output.txt`.

**Без этой строки:** WORKDIR был бы `/` (корень). Агент мог бы случайно создавать файлы в корне файловой системы (хотя пользователь `agent` не имеет туда прав).

### `COPY 05_production/agent.py /app/agent.py` и `COPY log_utils.py /app/log_utils.py`

**Что делает:** копирует Python-файлы в `/app/`. На этом шаге пользователь ещё `root`, поэтому `/app/` и все файлы в нём будут принадлежать `root`.

**Откуда берётся файл:** `05_production/agent.py` — из `browser_use/05_production/agent.py` (относительно context `..`). `log_utils.py` — из `browser_use/log_utils.py` (корневой).

**Почему `/app/`, а не `/workspace/`:** `/workspace` — это данные (bind-mount с хоста, может быть перезаписан). `/app/` — это код (только для чтения, в образе, не меняется при запуске). Разделение данных и кода.

**Критически важно:** файлы в `/app/` принадлежат `root` и пользователь `agent` не может туда писать. Агент может только **читать** код из `/app/`.

### `RUN useradd -m -u 1000 agent`

**Что делает:** создаёт пользователя `agent` с UID 1000 и домашней директорией `/home/agent` (флаг `-m`).

**Зачем UID 1000:** это стандартный UID первого обычного пользователя в Linux. Твой пользователь на хосте тоже скорее всего имеет UID 1000:
```bash
id -u  # скорее всего 1000
```
Это удобно для bind-mount: файлы созданные `agent` внутри контейнера будут принадлежать тебе на хосте (совпадение UID).

**Без этой строки:** следующий `USER agent` упал бы с ошибкой "unable to find user agent".

### `USER agent`

**Что делает:** все последующие команды в Dockerfile и финальный `CMD` будут выполняться от пользователя `agent`, а не `root`.

**Что меняется:** `agent` — обычный пользователь без sudo. Он не может:
- устанавливать пакеты (`apt-get install`)
- писать в директории принадлежащие `root` (например `/app/`)
- биндить порты < 1024

**Зачем:** principal of least privilege. Если агент запустит вредоносный код или браузер будет взломан — атакующий получит права обычного пользователя, не root. Из контейнера сложнее выбраться без root.

**Без этой строки:** всё работало бы от root. Docker не запрещает это, но это плохая практика в production.

### `CMD ["python", "/app/agent.py"]`

**Что делает:** задаёт команду которая запускается когда контейнер стартует. Это не выполнение при сборке — это инструкция "что делать при `docker run`".

**CMD vs RUN:** `RUN` выполняется во время `docker build` (создаёт слой образа). `CMD` выполняется во время `docker run` / `docker-compose up`.

**Формат `["python", "/app/agent.py"]`:** JSON-array (exec form). Процесс запускается напрямую без shell. Преимущество: `Ctrl+C` и Docker stop signals доходят до Python-процесса, а не до bash-обёртки.

---

## 3. docker-compose.yml — шаг за шагом

### `build: context: ..` и `dockerfile: 05_production/Dockerfile`

```yaml
build:
  context: ..
  dockerfile: 05_production/Dockerfile
```

**`context: ..`** — build context. Docker daemon получает содержимое этой папки для выполнения COPY-команд. Две точки = папка `browser_use/` (родитель `05_production/`).

Почему это важно: Dockerfile содержит `COPY log_utils.py /app/log_utils.py`. Этот файл лежит в `browser_use/log_utils.py`. Если context был бы `.` (05_production/), Docker не нашёл бы `log_utils.py` и сборка упала бы с ошибкой "file not found".

**`dockerfile: 05_production/Dockerfile`** — путь к Dockerfile относительно context. Раньше был просто `build: .` что означало: context=текущая папка, Dockerfile=`./Dockerfile`. Теперь context расширен, поэтому путь к Dockerfile нужно указывать явно.

### `env_file` vs `environment`

```yaml
env_file:
  - ../.env
environment:
  - USE_LOCAL_MODEL=false
  - OLLAMA_HOST=http://host.docker.internal:11434
  - AGENT_TASK=Зайди на coinmarketcap.com...
```

**`env_file`:** читает файл `.env` с хоста и загружает все переменные из него в контейнер. Файл не копируется в образ — только значения передаются как env vars. Это безопасно: секреты не попадают в слои Docker image.

**`environment`:** задаёт переменные прямо в docker-compose.yml. Это удобно для несекретных настроек которые можно менять без перезаписи .env.

**Приоритет при совпадении имён:** `environment` побеждает над `env_file`. Если в `.env` написано `USE_LOCAL_MODEL=true`, а в `environment` — `USE_LOCAL_MODEL=false`, контейнер получит `false`. Правило: `environment` в compose-файле имеет наивысший приоритет.

**Что попадает в контейнер:** объединение обоих источников. Агент видит как `ANTHROPIC_API_KEY` из `.env`, так и `AGENT_TASK` из `environment`.

### `volumes: - ./workspace:/workspace:rw`

```yaml
volumes:
  - ./workspace:/workspace:rw
```

**Синтаксис:** `<путь на хосте>:<путь в контейнере>:<режим>`.

`./workspace` — папка `05_production/workspace/` на хосте (относительно docker-compose.yml).
`/workspace` — та же папка но видна изнутри контейнера.
`:rw` — read-write, контейнер может читать и писать.

**Это bind-mount, не volume.** Разница:
- **bind-mount** (наш случай): жёсткая привязка к конкретному пути на хосте. Изменения в реальном времени видны с обеих сторон.
- **named volume** (`volumes: - mydata:/workspace`): Docker сам управляет хранилищем где-то в `/var/lib/docker/volumes/`. Ты не знаешь конкретный путь на хосте.

**Почему агент может писать в `/workspace` но не в `/app`:**
- `/app/` создан при `docker build` от пользователя `root` → принадлежит root → `agent` не может писать
- `/workspace/` примонтирована с хоста. Папка на хосте `05_production/workspace/` принадлежит тебе (UID 1000 = emkex). Пользователь `agent` в контейнере тоже UID 1000 → они эквивалентны → `agent` может писать в `/workspace`

### `security_opt`, `cap_drop`, `cap_add`

```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - SYS_ADMIN
```

**Linux capabilities** — гранулярные права root. Вместо "всё или ничего", Linux разбивает root-полномочия на ~40 возможностей: `NET_BIND_SERVICE` (биндить порты < 1024), `KILL` (убивать чужие процессы), `SYS_ADMIN` (монтирование, namespace-ы, cgroups), и т.д.

**`cap_drop: ALL`** — убираем вообще все capabilities. Контейнер стартует без каких-либо повышенных прав.

**`cap_add: SYS_ADMIN`** — возвращаем обратно только `SYS_ADMIN`. Почему именно она нужна Chromium: браузер использует namespace-ы и seccomp для sandbox каждой вкладки. Создание user namespaces требует `SYS_ADMIN` (или `--no-sandbox` flag, что небезопасно).

Альтернатива без `SYS_ADMIN`: запустить Chromium с флагом `--no-sandbox`. Это убирает изоляцию вкладок и не рекомендуется в production.

**`no-new-privileges: true`** — запрет на получение дополнительных прав через setuid-биты. Например, если бы в контейнере оказался `sudo` с setuid — он не смог бы повысить привилегии. Это второй эшелон защиты.

### `networks`

```yaml
networks:
  agent-net:
    driver: bridge
    enable_ipv6: false
```

**Bridge network** — виртуальный коммутатор. Docker создаёт виртуальный сетевой интерфейс `docker0` на хосте и подключает к нему контейнеры. Контейнеры в одной bridge-сети видят друг друга по hostname (имени сервиса). Контейнеры в разных bridge-сетях изолированы.

**Зачем своя сеть, а не default bridge:** в default bridge-сети контейнеры не резолвят друг друга по имени. В пользовательской сети (`agent-net`) `agent` мог бы достучаться до `squid-proxy` просто по hostname `squid-proxy`.

**`enable_ipv6: false`** — явное отключение IPv6. Это фикс для Docker Desktop on Linux где при смене этой настройки между запусками возникает ошибка "Network needs to be recreated".

**`internal: true` (закомментировано)** — если раскомментировать: контейнеры в этой сети не имеют доступа к интернету. Только к другим контейнерам в той же сети. Полезно если хочешь убедиться что агент ходит только через прокси.

---

## 4. Пути — полная карта

| Путь на хосте | Путь в контейнере | Доступ | Зачем |
|---|---|---|---|
| `browser_use/.env` | — (не файл, только значения) | env vars | секреты и настройки |
| `05_production/workspace/` | `/workspace/` | read-write | логи и результаты агента |
| (нет, в image) | `/app/agent.py` | read-only | основной код |
| (нет, в image) | `/app/log_utils.py` | read-only | утилиты логирования |
| (нет, в image) | `/home/agent/` | read-write | домашняя папка пользователя agent |
| (нет, в image) | `/tmp/` | read-write | временные файлы (Chromium profile) |

**Почему `/app/` read-only для пользователя `agent`:**

Во время `docker build` последовательность такая:
```
...шаги от root...
COPY agent.py /app/agent.py        # root создаёт /app/, файл принадлежит root
COPY log_utils.py /app/log_utils.py  # root владеет файлом
RUN useradd -m -u 1000 agent       # создаём пользователя
USER agent                         # переключаемся на agent
CMD [...]                          # запуск от agent
```

`/app/` создана root'ом → принадлежит root. Пользователь `agent` может читать файлы (права 644 по умолчанию), но не может создавать новые файлы или папки в `/app/`.

---

## 5. Найденная проблема с правами

### Где и что происходит

В `log_utils.py` строка 29:

```python
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
```

`__file__` в Docker = `/app/log_utils.py`
`Path(__file__).parent` = `/app/`
`log_dir` = `/app/logs/`

Когда агент запускается от пользователя `agent` и вызывает `setup_logging(...)`, Python пытается создать директорию `/app/logs/`. Но `/app/` принадлежит `root`. Результат:

```
PermissionError: [Errno 13] Permission denied: '/app/logs'
```

### Вариант A — исправить Dockerfile (рекомендуется)

Добавить явное создание папки и передачу прав до `USER agent`:

```dockerfile
COPY 05_production/agent.py /app/agent.py
COPY log_utils.py /app/log_utils.py

# Создаём папку для логов внутри контейнера и отдаём её agent
RUN mkdir -p /app/logs && chown -R agent:agent /app/logs

RUN useradd -m -u 1000 agent
USER agent
```

Плюс: логи пишутся в `/app/logs/` — предсказуемо, не зависит от PATH.
Минус: логи внутри контейнера, не видны на хосте (если не добавить ещё один bind-mount).

### Вариант B — исправить log_utils.py (рекомендуется для Docker)

Перенаправить логи в `/workspace/logs/`, куда у `agent` есть доступ через bind-mount:

```python
def setup_logging(script_name: str) -> logging.Logger:
    # Используем /workspace если доступен (Docker), иначе рядом со скриптом (локальный запуск)
    workspace = Path("/workspace")
    if workspace.exists() and os.access(workspace, os.W_OK):
        log_dir = workspace / "logs"
    else:
        log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    ...
```

Плюс: логи появляются в `05_production/workspace/logs/` на хосте — сразу видны без захода в контейнер.
Плюс: работает и локально, и в Docker без изменения Dockerfile.
Минус: код становится чуть сложнее.

**Рекомендация: Вариант B.** Логи в `workspace/` — это правильное место для артефактов агента. Они сразу доступны на хосте, не нужно `docker exec` чтобы их посмотреть. Dockerfile остаётся чистым.

---

## 6. Полный жизненный цикл контейнера

### `docker-compose up --build`

1. Docker читает `docker-compose.yml`, видит `build: context: ..`
2. Собирает build context — архивирует папку `browser_use/` и отправляет Docker daemon
3. Dockerfile выполняется слой за слоем (кешируются все слои кроме изменившихся)
4. Создаётся image `05_production_agent:latest`
5. Создаётся сеть `05_production_agent-net` (если не существует)
6. Docker читает `env_file: ../.env`, загружает переменные
7. Создаётся контейнер `05_production_agent_1` из image
8. Монтируется `./workspace:/workspace:rw`
9. Запускается `CMD ["python", "/app/agent.py"]` от пользователя `agent`
10. `agent.py` вызывает `load_dotenv(...)` — загружает `.env` ещё раз (дублирует, но не вредит)
11. `build_llm()` создаёт ChatAnthropic или ChatOllama
12. `build_browser_profile()` создаёт BrowserProfile (с прокси или без)
13. `HeaderAgent.run(max_steps=20)` запускает агента:
    - Playwright запускает Chromium headless внутри контейнера
    - Агент делает шаги: открывает страницу, читает DOM, принимает решения
    - Логи пишутся в stdout и в файл (если права позволяют)
14. После `max_steps` или завершения задачи — `save_run_summary()`
15. Python-процесс завершается → контейнер переходит в статус `Exited (0)` или `Exited (1)`

### `docker-compose up` (без `--build`)

Отличие: шаги 2–4 пропускаются. Используется уже существующий image. Изменения в `agent.py` на хосте **не подхватятся** — файл скопирован в image при сборке. Нужен `--build` после любых изменений кода.

Когда можно без `--build`: если изменилось только содержимое `.env` или `environment` в docker-compose.yml.

### `docker-compose down`

1. Останавливает все контейнеры проекта (SIGTERM → SIGKILL через 10 сек)
2. Удаляет контейнеры
3. Удаляет сеть `05_production_agent-net`
4. **НЕ удаляет:** image, volumes, содержимое `workspace/` на хосте

### `docker ps -a` после завершения

```
CONTAINER ID  IMAGE                  COMMAND               STATUS
3b549928a89f  05_production_agent    "python /app/agent.py"  Exited (1) 6 minutes ago
```

`Exited (1)` — нормально для batch-задачи (агент выполнил задачу и завершился). Код выхода `1` означает ошибку (в нашем случае — PermissionError с логами). Код `0` = успешное завершение.

`Exited` vs `Up`: контейнер должен быть в `Up` постоянно только если это сервер (веб-сервис, база данных). Агент-скрипт запустился, выполнил задачу, вышел — это нормально.

Остановленный контейнер занимает место на диске и его можно удалить: `docker container prune`.

---

## 7. host.docker.internal

В `docker-compose.yml`:
```yaml
- OLLAMA_HOST=http://host.docker.internal:11434
```

**Что это:** специальный DNS-адрес, который Docker резолвит в IP-адрес хост-машины. Контейнер не может написать `localhost:11434` потому что внутри контейнера `localhost` — это сам контейнер, у которого нет Ollama.

**Как это работает:**

```
Хост (твой компьютер)
├── Ollama → слушает на 127.0.0.1:11434
└── Docker
    └── Контейнер agent
        ├── localhost → 127.0.0.1 (контейнера, не хоста!)
        └── host.docker.internal → 192.168.65.254 (IP хоста в виртуальной сети Docker)
```

**Отличия по платформам:**

| Платформа | host.docker.internal | Примечание |
|---|---|---|
| Mac (Docker Desktop) | работает из коробки | Docker Desktop добавляет автоматически |
| Windows (Docker Desktop) | работает из коробки | аналогично Mac |
| Linux (Docker Desktop) | работает из коробки | Docker Desktop создаёт виртуальную сеть |
| Linux (Docker Engine, без Desktop) | **не работает по умолчанию** | нужно добавить `--add-host=host.docker.internal:host-gateway` в docker-compose |

На Linux без Docker Desktop добавить в docker-compose.yml:
```yaml
services:
  agent:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

---

## 8. Команды для ежедневной работы

```bash
# Первый запуск или после изменения Dockerfile / requirements.txt / agent.py
docker-compose up --build

# Запуск без пересборки — только если изменился .env или AGENT_TASK в docker-compose
# ВНИМАНИЕ: agent.py скопирован в image, изменения на хосте не подхватятся без --build
docker-compose up

# Запустить в фоне (detached mode)
docker-compose up -d --build

# Смотреть логи в реальном времени (если запущен в фоне)
docker-compose logs -f

# Остановить и убрать контейнеры + сети
docker-compose down

# Убрать ещё и orphan-контейнеры (если были ошибки с compose)
docker-compose down --remove-orphans

# Зайти внутрь работающего контейнера (если запущен как сервис, не batch)
docker-compose exec agent bash

# Зайти внутрь остановленного контейнера для отладки
docker run -it --rm 05_production_agent bash

# Посмотреть логи агента на хосте (если логи в workspace)
ls -la ./workspace/logs/
cat ./workspace/logs/production_*.log

# Посмотреть что внутри контейнера
docker run -it --rm 05_production_agent ls -la /app/

# Принудительно пересобрать с нуля (сбросить кеш)
docker-compose build --no-cache
docker-compose up

# Удалить образ и пересобрать
docker rmi 05_production_agent
docker-compose up --build

# Убрать все остановленные контейнеры
docker container prune

# Убрать неиспользуемые образы
docker image prune

# Фикс ошибки "Network needs to be recreated"
docker network rm 05_production_agent-net
docker-compose up --build
```

---

## 9. Разбор ошибок из истории запусков

### `ModuleNotFoundError: No module named 'log_utils'`

**Причина:** в Dockerfile изначально было только `COPY agent.py /app/agent.py`. Файл `log_utils.py` не был скопирован в образ. При импорте `from log_utils import ...` Python искал модуль в `/app/` (через sys.path который добавляет `..` от `/app/agent.py`) и не находил.

**Как была исправлена:** изменён build context на `..` (browser_use/) и добавлена строка `COPY log_utils.py /app/log_utils.py` в Dockerfile.

### `PermissionError: [Errno 13] Permission denied: '/app/logs'`

**Причина:** `log_utils.py` строка 29 вычисляет путь к логам как `Path(__file__).parent / "logs"` = `/app/logs/`. Директория `/app/` принадлежит `root` (создана при сборке образа до переключения `USER agent`). Пользователь `agent` не имеет прав создавать папки в `/app/`.

**Как исправить:** см. раздел 5 — Вариант B (перенаправить логи в `/workspace/logs/`).

### `Network "05_production_agent-net" needs to be recreated - option "com.docker.network.enable_ipv4/ipv6" has changed`

**Почему возникает:** Docker Desktop сохраняет метаданные сети (IPv4/IPv6 флаги). Если между запусками изменилась версия Docker или настройки сети в docker-compose.yml, Docker обнаруживает расхождение с сохранёнными метаданными и не пересоздаёт сеть автоматически.

В нашем случае это усугублялось тем, что один из промежуточных `docker-compose up` упал на полпути — сеть была создана с дефолтными настройками, а потом в docker-compose добавили `enable_ipv6: false`. Конфликт.

**Стандартное решение:**
```bash
docker network rm 05_production_agent-net
docker-compose up --build
```

**Долгосрочный фикс:** явно задать `enable_ipv6: false` в docker-compose.yml — тогда при создании сети настройки будут всегда одинаковые.

### `Found orphan containers (05_production_squid-proxy_1)`

**Что такое orphan container:** контейнер который был создан этим же docker-compose проектом (тот же project name `05_production`), но для сервиса которого уже нет в текущем docker-compose.yml.

**Когда возникает:** сервис `squid-proxy` был закомментирован в docker-compose.yml, но его контейнер (`05_production_squid-proxy_1`) уже существовал от предыдущего запуска когда squid был активен. Docker видит "этот контейнер из того же проекта, но его сервиса нет в compose — подозрительно".

**Решение:** `docker-compose down --remove-orphans` или `docker-compose up --remove-orphans`.

---

## Итоговая схема

```
═══════════════════════════════════════════════════════════════════════
  ХОСТ (emkex@emkex-Latitude-5500)
═══════════════════════════════════════════════════════════════════════

  ~/browser_use/
  ├── .env ──────────────────────────────────────────────────────────┐
  │   ANTHROPIC_API_KEY=...                                          │ env_file
  │   AGENT_TASK=...                                                 │
  │                                                                  ▼
  └── 05_production/                             ╔══════════════════════════════╗
      ├── docker-compose.yml ──── build ────────▶║  IMAGE 05_production_agent  ║
      ├── Dockerfile                             ║  /app/agent.py   (root)      ║
      ├── requirements.txt                       ║  /app/log_utils.py (root)    ║
      ├── agent.py ──── COPY ──────────────────▶ ║  python 3.12 + Chromium      ║
      │                                          ╚══════════════════════════════╝
  ~/browser_use/                                           │
      └── log_utils.py ── COPY ────────────────────────────┘
                                                           │ docker-compose up
                                             ╔═════════════▼═══════════════════╗
                                             ║  КОНТЕЙНЕР 05_production_agent  ║
  05_production/workspace/ ◀══ bind-mount ══▶║  /workspace/    (agent:rw)      ║
                                             ║  /app/          (root:ro)        ║
                                             ║                                  ║
                                             ║  USER: agent (UID 1000)          ║
                                             ║  CMD: python /app/agent.py       ║
                                             ║                                  ║
                                             ║  Chromium (headless)             ║
                                             ║    │ если HTTPS_PROXY задан      ║
                                             ║    ▼                             ║
                                             ║  [squid-proxy:3128] (опц.)       ║
                                             ╚══════════════════╤══════════════╝
                                                                │
                                               agent-net (bridge, no-ipv6)
                                                                │
                                             ╔══════════════════▼══════════════╗
                                             ║         ИНТЕРНЕТ                 ║
                                             ║  coinmarketcap.com               ║
                                             ║  yahoo.com                       ║
                                             ║  api.anthropic.com               ║
                                             ╚══════════════════════════════════╝

  host.docker.internal ──────────────────────────────▶ Ollama :11434 (на хосте)

  Потоки данных:
  .env ──────────────────────────────────▶ env vars в контейнере
  agent.py + log_utils.py ──── build ───▶ /app/ в image (read-only)
  workspace/ ◀────── bind-mount ────────▶ /workspace/ (read-write)
  логи ─────────────────────────────────▶ stdout + /workspace/logs/*.log
```

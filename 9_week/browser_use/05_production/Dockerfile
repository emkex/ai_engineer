FROM python:3.12-slim

# Системные зависимости для Playwright/Chromium
RUN apt-get update -qq && apt-get install -y -qq \
    curl wget gnupg \
    && rm -rf /var/lib/apt/lists/*

# Python-зависимости
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Chromium через playwright (не системный — контролируемая версия)
RUN playwright install chromium --with-deps

# Рабочая директория — только /workspace будет доступна агенту
# В docker-compose она bind-mounted с хоста (read-write)
WORKDIR /workspace

COPY agent.py /app/agent.py

# Запускаем от непривилегированного пользователя
RUN useradd -m -u 1000 agent
USER agent

CMD ["python", "/app/agent.py"]

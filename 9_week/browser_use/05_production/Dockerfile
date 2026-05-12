FROM python:3.12-slim

# Системные зависимости для Playwright/Chromium
RUN apt-get update -qq && apt-get install -y -qq \
    curl wget gnupg \
    && rm -rf /var/lib/apt/lists/*

# Python-зависимости
COPY 05_production/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Chromium в общую папку — доступна всем пользователям, не только root
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium --with-deps && chmod -R 755 /ms-playwright

# Рабочая директория — только /workspace будет доступна агенту
# В docker-compose она bind-mounted с хоста (read-write)
WORKDIR /workspace

COPY 05_production/agent.py /app/agent.py
COPY 05_production/log_utils.py /app/log_utils.py

# Запускаем от непривилегированного пользователя
RUN useradd -m -u 1000 agent
USER agent

CMD ["python", "/app/agent.py"]

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Устанавливаем пакеты + Chromium для Playwright (--with-deps ставит системные либы)
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

COPY . .

CMD ["python", "src/app.py"]
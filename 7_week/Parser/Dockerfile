# Официальный образ Microsoft: Ubuntu 22.04 + Python 3.11 + Chromium уже внутри
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY requirements.txt .

# playwright уже установлен в базовом образе — ставим только остальные пакеты
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "src/app.py"]
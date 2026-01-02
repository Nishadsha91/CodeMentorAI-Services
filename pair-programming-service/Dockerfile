FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD python manage.py migrate && \
    daphne -b 0.0.0.0 -p 8007 pair_service.asgi:application
FROM python:3.11-slim

WORKDIR /app

# Instala dependências de compilação para psycopg2 e rede
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python -m app.sync seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

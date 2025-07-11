FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.prod.txt .

RUN pip install --no-cache-dir --target=/build/dependencies -r requirements.prod.txt

FROM python:3.11-slim AS production

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser && \
    apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/dependencies /usr/local/lib/python3.11/site-packages/

COPY app/ ./app/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
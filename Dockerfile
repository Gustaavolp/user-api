FROM python:3.11-alpine AS builder

WORKDIR /build

COPY requirements.prod.txt .

RUN apk add --no-cache gcc musl-dev && \
    pip install --no-cache-dir --target=/build/dependencies -r requirements.prod.txt && \
    apk del gcc musl-dev

FROM python:3.11-alpine AS production

RUN addgroup -g 1000 appuser && \
    adduser -u 1000 -G appuser -s /bin/sh -D appuser && \
    apk add --no-cache curl

WORKDIR /app

RUN chown appuser:appuser /app

COPY --from=builder /build/dependencies /usr/local/lib/python3.11/site-packages/

COPY --chown=appuser:appuser app/ ./app/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
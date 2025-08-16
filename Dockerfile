FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=4000

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    "uvicorn[standard]==0.30.6"

COPY app.py /app/app.py

# 非rootユーザーで実行
RUN useradd -r -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

LABEL org.opencontainers.image.title="json-echo" \
      org.opencontainers.image.description="Return static JSON/HTML/TXT by first path segment." \
      org.opencontainers.image.licenses="MIT"

EXPOSE 4000

CMD ["sh","-c","uvicorn app:app --host 0.0.0.0 --port ${PORT}"]

# Backend Celery / 开发 compose 用镜像（与根 Dockerfile production 目标对齐）
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --no-deps -r requirements.lock

COPY . .

ENV FFMPEG_PATH=/usr/bin/ffmpeg
ENV FFPROBE_PATH=/usr/bin/ffprobe

# 非 root 用户运行保障安全
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# WAF 黑名单拦裸 curl UA（403），healthcheck 必须用白名单 UA
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f -A "YouDingSaaS-Internal/1.0" http://localhost:8000/health/ready || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]

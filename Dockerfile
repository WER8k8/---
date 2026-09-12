# ============================================================
# Youding Backend — Python FastAPI 生产镜像
# 藏云阁加速（可选）:
#   docker build --build-arg BASE_IMAGE=registry.cncfstack.com/docker.io/library/python:3.11-slim .
# 文档: https://cncfstack.com/p/assets/docs/cncfstack/image/
# ============================================================
ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE} AS base

WORKDIR /app

# 系统依赖（ffmpeg 供中文片出海配音/烧录；生产不依赖宿主机 WinGet）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============================================================
# 开发阶段
# ============================================================
FROM base AS development

COPY backend/ .

ENV FFMPEG_PATH=/usr/bin/ffmpeg
ENV FFPROBE_PATH=/usr/bin/ffprobe

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================
# 生产阶段
# ============================================================
FROM base AS production

COPY backend/ .

ENV FFMPEG_PATH=/usr/bin/ffmpeg
ENV FFPROBE_PATH=/usr/bin/ffprobe

# 非 root 用户运行
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ready || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]

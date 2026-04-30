# Docker 与 CI/CD 配置

## Docker Compose (docker-compose.yml)

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: ${DOCKER_TARGET:-development}
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NUXT_PUBLIC_API_BASE=http://backend:8000/api/v1
      - NUXT_PUBLIC_SITE_URL=https://youding.com
    depends_on:
      - backend
    networks:
      - app-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: ${DOCKER_TARGET:-development}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://youding:youding123@postgres:5432/youding_seo
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=youding_admin
      - MINIO_SECRET_KEY=youding_secret_key
      - JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
      - AI_OPENAI_API_KEY=${AI_OPENAI_API_KEY}
      - AI_ANTHROPIC_API_KEY=${AI_ANTHROPIC_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  postgres:
    image: postgres:15.6
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=youding_seo
      - POSTGRES_USER=youding
      - POSTGRES_PASSWORD=youding123
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U youding"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  redis:
    image: redis:7.2.4
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=youding_admin
      - MINIO_ROOT_PASSWORD=youding_secret_key
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  app-network:
    driver: bridge
```

## 前端 Dockerfile

```dockerfile
# 开发阶段
FROM node:20-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# 构建阶段
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 生产阶段
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=build /app/.output ./.output
COPY --from=build /app/package.json ./
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
```

## 后端 Dockerfile

```dockerfile
# 开发阶段
FROM python:3.11-slim AS development
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 生产阶段
FROM python:3.11-slim AS production
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## CI/CD (GitHub Actions)

```yaml
name: Stage 1 CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Frontend lint
        working-directory: frontend
        run: |
          npm install
          npm run lint
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: backend/requirements.txt
      
      - name: Backend lint
        working-directory: backend
        run: |
          pip install ruff
          ruff check app/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15.6
        env:
          POSTGRES_DB: youding_test
          POSTGRES_USER: youding
          POSTGRES_PASSWORD: youding123
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7.2.4
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Backend tests
        working-directory: backend
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov
          pytest --cov=app --cov-report=xml
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Frontend unit tests
        working-directory: frontend
        run: |
          npm install
          npm run test

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build frontend
        working-directory: frontend
        run: |
          npm install
          npm run build
      
      - name: Build Docker images
        run: |
          docker compose build
```

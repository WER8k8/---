# 前端 Admin Docker 构建（藏云阁镜像可选）
# docker build --build-arg NODE_IMAGE=registry.cncfstack.com/docker.io/library/node:18-alpine .
ARG NODE_IMAGE=node:18-alpine
ARG NGINX_IMAGE=nginx:1.27-alpine

FROM ${NODE_IMAGE} AS builder

WORKDIR /app

COPY admin/package.json admin/package-lock.json* ./
# 构建需要 devDependencies（vue-tsc / vite）
RUN npm install

COPY admin/ ./
COPY config/ /config/
COPY utils/ /utils/
COPY youding-admin-kit/ /youding-admin-kit/

RUN npm run build

FROM ${NGINX_IMAGE}

COPY --from=builder /app/dist /usr/share/nginx/html
COPY admin/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

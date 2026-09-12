#!/bin/bash
# ============================================================
# 优丁建材 SaaS 系统 — 一键生产部署脚本
# ============================================================
# 用法:
#   chmod +x deploy/deploy.sh
#   ./deploy/deploy.sh                    # 交互式部署
#   DOMAIN=youding.com ./deploy/deploy.sh # 指定域名
#   ./deploy/deploy.sh --skip-ssl         # 跳过 SSL 配置
#   ./deploy/deploy.sh --verify-only      # 仅验证不部署
# ============================================================
set -euo pipefail

# ----------------------------------------------------------
# 颜色输出
# ----------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "\n${CYAN}════════════════════════════════════════${NC}"; echo -e "${CYAN}  $*${NC}"; echo -e "${CYAN}════════════════════════════════════════${NC}\n"; }
log_title() {
    echo -e "${BLUE}"
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║       优丁建材 AI-SaaS 一键部署系统         ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ----------------------------------------------------------
# 参数解析
# ----------------------------------------------------------
SKIP_SSL=false
VERIFY_ONLY=false
DOMAIN="${DOMAIN:-youding.com}"
ENV_FILE=".env.prod"
COMPOSE_FILE="docker-compose.prod.yml"
DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$DEPLOY_DIR")"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-ssl)    SKIP_SSL=true; shift ;;
        --verify-only) VERIFY_ONLY=true; shift ;;
        --domain)      DOMAIN="$2"; shift 2 ;;
        --env-file)    ENV_FILE="$2"; shift 2 ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo "  --skip-ssl       跳过 SSL/Let's Encrypt 配置"
            echo "  --verify-only    仅运行验证，不部署"
            echo "  --domain DOMAIN  指定域名 (默认: youding.com)"
            echo "  --env-file FILE  指定环境变量文件 (默认: .env.prod)"
            exit 0
            ;;
        *) log_error "未知参数: $1"; exit 1 ;;
    esac
done

log_title
cd "$PROJECT_ROOT"

# ============================================================
# Step 0: 环境检查
# ============================================================
log_step "Step 0/8: 环境检查"

REQUIRED_COMMANDS=("docker" "docker-compose" "curl" "openssl")
MISSING=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" &>/dev/null; then
        MISSING+=("$cmd")
    else
        log_info "✓ $cmd $(command -v "$cmd")"
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    log_error "缺少依赖: ${MISSING[*]}"
    log_info "请运行: sudo apt-get install -y docker.io docker-compose-v2 curl openssl"
    exit 1
fi

# Docker 运行状态检查
if ! docker info &>/dev/null; then
    log_error "Docker 守护进程未运行"
    log_info "请运行: sudo systemctl start docker"
    exit 1
fi
log_info "✓ Docker daemon 运行中"

# 磁盘空间检查 (至少 10GB 可用)
AVAIL_GB=$(df -BG "$PROJECT_ROOT" | awk 'NR==2{print $4}' | sed 's/G//')
if [[ ${AVAIL_GB:-0} -lt 10 ]]; then
    log_warn "磁盘可用空间仅 ${AVAIL_GB}G (建议 >= 10G)"
fi
log_info "✓ 磁盘可用: ${AVAIL_GB}G"

# 内存检查 (至少 4GB)
TOTAL_MEM_MB=$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
if [[ ${TOTAL_MEM_MB:-0} -lt 3800 ]]; then
    log_warn "内存仅 ${TOTAL_MEM_MB}M (建议 >= 4G)"
else
    log_info "✓ 内存: ${TOTAL_MEM_MB}M"
fi

# ============================================================
# Step 1: 加载环境变量
# ============================================================
log_step "Step 1/8: 环境变量配置"

if [[ ! -f "$ENV_FILE" ]]; then
    log_warn "$ENV_FILE 不存在，从模板创建..."

    # 生成强随机密钥
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    MINIO_ACCESS_KEY="admin"
    MINIO_SECRET_KEY=$(openssl rand -hex 16)

    cat > "$ENV_FILE" << PRODENVEOF
# ============================================================
# 优丁建材 生产环境变量 — 自动生成 $(date '+%Y-%m-%d %H:%M:%S')
# 请立即修改标记为 [必须修改] 的项!!
# ============================================================

# --- 域名 [必须修改] ---
DOMAIN=${DOMAIN}

# --- 数据库 ---
DB_NAME=youding_prod
DB_USER=youding_admin
DB_PASSWORD=${DB_PASSWORD}

# --- Redis ---
REDIS_PASSWORD=${REDIS_PASSWORD}

# --- JWT (已自动生成) ---
JWT_SECRET_KEY=${JWT_SECRET}

# --- MinIO 对象存储 ---
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY}

# --- 邮件 [必须修改] ---
SMTP_SERVER=smtp.exmail.qq.com
SMTP_PORT=587
SMTP_USERNAME=noreply@youding.com
SMTP_PASSWORD=your-smtp-password
FROM_EMAIL=noreply@youding.com

# --- AI API 密钥 [必须修改] ---
AI_NVIDIA_API_KEY=your-nvidia-api-key
# 英伟达免费通道模型探测：ENVIRONMENT=production 时后端自动开启，无需 NVIDIA_CUSTOMER_PROBE_SCHEDULER_ENABLED

# --- Grafana (监控面板) ---
GRAFANA_PASSWORD=$(openssl rand -hex 8)
PRODENVEOF

    log_info "✓ 已生成 $ENV_FILE，请编辑敏感配置后重新运行"
    log_warn "请务必修改: SMTP_PASSWORD, AI_NVIDIA_API_KEY, GRAFANA_PASSWORD"
    exit 0
fi

# 加载环境变量
set -a
source "$ENV_FILE"
set +a

# 验证必要变量
REQUIRED_VARS=("DOMAIN" "DB_NAME" "DB_USER" "DB_PASSWORD" "REDIS_PASSWORD" "JWT_SECRET_KEY")
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        MISSING_VARS+=("$var")
    fi
done
if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
    log_error "缺少必要环境变量: ${MISSING_VARS[*]}"
    log_info "请编辑 $ENV_FILE 补充后重新运行"
    exit 1
fi
log_info "✓ 环境变量验证通过 (${#REQUIRED_VARS[@]} 项)"

# JWT 密钥强度检查
JWT_KEY_LEN=${#JWT_SECRET_KEY}
if [[ $JWT_KEY_LEN -lt 32 ]]; then
    log_error "JWT_SECRET_KEY 太短 (${JWT_KEY_LEN} 字符, 要求 >= 32)"
    exit 1
fi
log_info "✓ JWT 密钥强度: ${JWT_KEY_LEN} 字符"

# 弱密码检测
WEAK_PATTERNS=("changeme" "change-me" "your-password" "your-secret" "your-key" "123456" "password")
for var_name in JWT_SECRET_KEY REDIS_PASSWORD MINIO_SECRET_KEY SMTP_PASSWORD; do
    val_lower=$(echo "${!var_name:-}" | tr '[:upper:]' '[:lower:]')
    for pat in "${WEAK_PATTERNS[@]}"; do
        if [[ "$val_lower" == *"$pat"* ]]; then
            log_error "$var_name 包含弱密码模式 '$pat'，请更换"
            exit 1
        fi
    done
done
log_info "✓ 弱密码检测通过"

# ============================================================
# Step 2: SSL 证书配置
# ============================================================
log_step "Step 2/8: SSL 证书配置"

SSL_DIR="$PROJECT_ROOT/deploy/ssl"
CERT_PATH="$SSL_DIR/fullchain.pem"
KEY_PATH="$SSL_DIR/privkey.pem"

if [[ "$SKIP_SSL" == "true" ]]; then
    log_warn "跳过 SSL 配置 (--skip-ssl)"
else
    mkdir -p "$SSL_DIR"

    if [[ -f "$CERT_PATH" ]] && [[ -f "$KEY_PATH" ]]; then
        # 检查证书是否在有效期内
        if openssl x509 -checkend 2592000 -noout -in "$CERT_PATH" 2>/dev/null; then
            log_info "✓ SSL 证书有效 (过期时间 > 30天)"
            SSL_READY=true
        else
            log_warn "SSL 证书已过期或即将过期，尝试续期..."
            SSL_READY=false
        fi
    else
        log_warn "SSL 证书未找到: $SSL_DIR"
        SSL_READY=false
    fi

    if [[ "$SSL_READY" != "true" ]]; then
        # 尝试 Let's Encrypt / Certbot
        if command -v certbot &>/dev/null; then
            log_info "使用 Certbot 获取 Let's Encrypt 证书..."
            log_info "请确保域名 $DOMAIN 已解析到本服务器"

            read -r -p "域名 ${DOMAIN} 的 DNS 已指向本服务器? [y/N] " dns_confirm
            if [[ "$dns_confirm" =~ ^[Yy]$ ]]; then
                sudo certbot certonly --standalone \
                    -d "$DOMAIN" \
                    -d "www.${DOMAIN}" \
                    --non-interactive --agree-tos \
                    --email "admin@${DOMAIN}" 2>/dev/null || {
                        log_warn "Certbot standalone 失败，尝试 webroot 模式..."
                        mkdir -p /var/www/certbot
                        sudo certbot certonly --webroot -w /var/www/certbot \
                            -d "$DOMAIN" -d "www.${DOMAIN}" \
                            --non-interactive --agree-tos \
                            --email "admin@${DOMAIN}" || true
                    }

                # 复制证书到 deploy/ssl/
                LE_DIR="/etc/letsencrypt/live/${DOMAIN}"
                if [[ -f "$LE_DIR/fullchain.pem" ]]; then
                    sudo cp "$LE_DIR/fullchain.pem" "$CERT_PATH"
                    sudo cp "$LE_DIR/privkey.pem" "$KEY_PATH"
                    sudo chown "$(id -u):$(id -g)" "$CERT_PATH" "$KEY_PATH"
                    chmod 600 "$KEY_PATH"
                    log_info "✓ SSL 证书已安装到 $SSL_DIR"
                else
                    log_error "Certbot 证书获取失败"
                    log_info "您可以稍后手动运行: sudo certbot certonly --standalone -d $DOMAIN"
                    log_info "或使用 --skip-ssl 跳过 SSL 配置"
                    exit 1
                fi
            else
                log_warn "跳过 Let's Encrypt，将使用自签名证书作为临时方案"
                log_info "请确保 DNS 解析后用 certbot 获取正式证书"

                # 生成自签名证书作为占位
                openssl req -x509 -nodes -days 90 -newkey rsa:2048 \
                    -keyout "$KEY_PATH" \
                    -out "$CERT_PATH" \
                    -subj "/CN=${DOMAIN}/O=Youding/C=CN" 2>/dev/null
                chmod 600 "$KEY_PATH"
                log_warn "已生成自签名证书 (有效期 90 天, 浏览器会警告不安全)"
            fi
        else
            log_warn "Certbot 未安装，生成自签名证书"
            openssl req -x509 -nodes -days 90 -newkey rsa:2048 \
                -keyout "$KEY_PATH" \
                -out "$CERT_PATH" \
                -subj "/CN=${DOMAIN}/O=Youding/C=CN" 2>/dev/null
            chmod 600 "$KEY_PATH"
        fi
    fi
fi

# 检查 Nginx SSL 配置中的证书路径
NGINX_SSL_CONF="$PROJECT_ROOT/deploy/nginx-prod.conf"
if [[ -f "$NGINX_SSL_CONF" ]]; then
    log_info "✓ Nginx 生产配置已就绪: $NGINX_SSL_CONF"
fi

# ============================================================
# Step 3: 构建 Docker 镜像
# ============================================================
log_step "Step 3/8: Docker 镜像构建"

log_info "构建后端镜像 (FastAPI)..."
docker build -t youding-backend:prod \
    -f Dockerfile \
    --target production \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    . 2>&1 | tail -5

log_info "构建前端 Nuxt 镜像 (SSG)..."
if [[ -f frontend/Dockerfile ]]; then
    docker build -t youding-frontend:prod \
        -f frontend/Dockerfile \
        frontend/ 2>&1 | tail -5
else
    log_warn "frontend/Dockerfile 不存在，跳过前端镜像构建"
fi

log_info "构建 Admin SPA 镜像..."
if [[ -f frontend/admin/Dockerfile ]]; then
    docker build -t youding-admin:prod \
        -f frontend/admin/Dockerfile \
        frontend/admin/ 2>&1 | tail -5
else
    log_warn "frontend/admin/Dockerfile 不存在，跳过 Admin 镜像构建"
fi

log_info "✓ 镜像构建完成"
docker images | grep youding | head -5

# ============================================================
# Step 4: 停止旧服务
# ============================================================
log_step "Step 4/8: 停止旧服务 (如有)"

if docker ps -q --filter "name=youding" 2>/dev/null | grep -q .; then
    log_info "停止现有容器..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans 2>/dev/null || true
    log_info "✓ 旧服务已停止"
else
    log_info "✓ 无运行中的旧服务"
fi

# ============================================================
# Step 5: 数据库迁移
# ============================================================
log_step "Step 5/8: 数据库准备与迁移"

log_info "启动数据库服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis 2>&1 | tail -3

log_info "等待 PostgreSQL 就绪 (最多 60 秒)..."
for i in $(seq 1 30); do
    if docker exec youding-postgres pg_isready -U "${DB_USER}" -d "${DB_NAME}" &>/dev/null; then
        log_info "✓ PostgreSQL 就绪 (${i}s)"
        break
    fi
    sleep 2
    if [[ $i -eq 30 ]]; then
        log_error "PostgreSQL 启动超时"
        docker logs youding-postgres --tail 20
        exit 1
    fi
done

log_info "等待 Redis 就绪..."
docker exec youding-redis redis-cli -a "${REDIS_PASSWORD}" ping &>/dev/null && \
    log_info "✓ Redis 就绪" || \
    log_warn "Redis 检查失败 (可能密码不匹配)"

# 运行数据库迁移
log_info "运行 Alembic 数据库迁移..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm \
    backend alembic upgrade head 2>&1 | tail -10 || log_warn "Alembic 迁移警告 (可能数据库已是最新)"

# 种子数据
log_info "执行种子数据初始化..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm \
    backend python seed.py 2>&1 | tail -5 || log_warn "种子数据初始化警告"

log_info "✓ 数据库迁移完成"

# ============================================================
# Step 6: 启动全部服务
# ============================================================
log_step "Step 6/8: 启动全部服务"

log_info "启动所有生产服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --remove-orphans 2>&1 | tail -5

log_info "等待服务健康检查 (最多 120s)..."
sleep 5

# 等待后端健康
for i in $(seq 1 24); do
    if curl -sf http://localhost:8000/health &>/dev/null; then
        log_info "✓ 后端健康检查通过 (${i})"
        break
    fi
    sleep 5
    if [[ $i -eq 24 ]]; then
        log_error "后端健康检查超时"
        docker logs youding-backend --tail 30
        echo "---"
        docker ps -a --filter "name=youding"
        exit 1
    fi
done

# 等待 Nginx
if curl -sf http://localhost:80/healthz &>/dev/null; then
    log_info "✓ Nginx 健康检查通过"
else
    log_warn "Nginx 健康检查失败 (可能在启动中)"
fi

# ============================================================
# Step 7: Nginx 配置重载
# ============================================================
log_step "Step 7/8: Nginx 配置验证与重载"

if docker exec youding-nginx nginx -t 2>&1 | tail -3; then
    log_info "✓ Nginx 配置验证通过"
    docker exec youding-nginx nginx -s reload 2>/dev/null || true
else
    log_error "Nginx 配置语法错误"
    exit 1
fi

# ============================================================
# Step 8: 部署验证
# ============================================================
log_step "Step 8/8: 部署验证"

echo ""
log_info "=== 服务状态 ==="
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker ps --filter "name=youding" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
log_info "=== 健康检查 ==="

# 后端健康
if curl -sf http://localhost:8000/health &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} 后端 API (localhost:8000/health)"
else
    echo -e "  ${RED}✗${NC} 后端 API (localhost:8000/health)"
fi

# API v1 健康
if curl -sf http://localhost:8000/api/v1/health &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} API v1 (/api/v1/health)"
else
    echo -e "  ${RED}✗${NC} API v1 (/api/v1/health)"
fi

# Nginx 健康
if curl -sf http://localhost:80/healthz &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Nginx (localhost:80/healthz)"
else
    echo -e "  ${RED}✗${NC} Nginx (localhost:80/healthz)"
fi

# HTTPS (如果 SSL 配置)
if [[ "$SKIP_SSL" != "true" ]]; then
    if curl -sfk https://localhost:443/healthz &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} HTTPS (localhost:443/healthz)"
    else
        echo -e "  ${YELLOW}⚠${NC} HTTPS (localhost:443/healthz) — 可能需要外部域名"
    fi
fi

# 数据库连接
if docker exec youding-postgres pg_isready -U "${DB_USER}" -d "${DB_NAME}" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL (5432)"
else
    echo -e "  ${RED}✗${NC} PostgreSQL (5432)"
fi

# Redis
if docker exec youding-redis redis-cli -a "${REDIS_PASSWORD}" ping &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Redis (6379)"
else
    echo -e "  ${RED}✗${NC} Redis (6379)"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  部署完成!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  访问地址:"
echo "    主站:     https://${DOMAIN}"
echo "    Admin:    https://${DOMAIN}/admin"
echo "    API文档:  https://${DOMAIN}/docs"
echo "    Grafana:  http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'SERVER_IP'):3000"
echo ""
echo "  管理命令:"
echo "    查看日志:  docker compose -f $COMPOSE_FILE logs -f backend"
echo "    重启服务:  docker compose -f $COMPOSE_FILE restart"
echo "    停止全部:  docker compose -f $COMPOSE_FILE down"
echo "    数据库备份: docker exec youding-db-backup pg_dump -h postgres -U ${DB_USER} ${DB_NAME} | gzip > backup_\$(date +%Y%m%d_%H%M%S).sql.gz"
echo ""
echo "  安全提醒:"
echo "    - 请修改默认密码 (如有)"
echo "    - 配置防火墙仅开放 80/443 端口"
echo "    - 定期更新 SSL 证书 (certbot renew)"
echo "    - 定期备份数据库"
echo ""

# ============================================================
# Step 9: 云上自动展开（Agency LLM + Hermes 首巡站）
# ============================================================
if [[ "${SKIP_POST_DEPLOY:-0}" != "1" ]] && [[ -f "$PROJECT_ROOT/scripts/cloud-post-deploy.sh" ]]; then
    log_step "Step 9/9: 云上自动展开（Agency LLM + Hermes 自愈齿轮）"
    chmod +x "$PROJECT_ROOT/scripts/cloud-post-deploy.sh" 2>/dev/null || true
    export HERMES_AGENCY_AUTO_DOCKER_OLLAMA="${HERMES_AGENCY_AUTO_DOCKER_OLLAMA:-1}"
    bash "$PROJECT_ROOT/scripts/cloud-post-deploy.sh" || log_warn "cloud-post-deploy 部分步骤失败（可稍后手动 bash scripts/cloud-post-deploy.sh）"
fi

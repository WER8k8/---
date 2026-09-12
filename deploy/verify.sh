#!/bin/bash
# ============================================================
# 优丁建材 — 部署后验证脚本
# ============================================================
# 用法:
#   chmod +x deploy/verify.sh
#   ./deploy/verify.sh                    # 验证 localhost
#   DOMAIN=youding.com ./deploy/verify.sh # 验证指定域名
#   ./deploy/verify.sh --verbose          # 详细输出
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0
VERBOSE=false
TIMEOUT=10
MAX_RETRIES=2
BASE_URL="${BASE_URL:-http://localhost}"
API_URL="${API_URL:-http://localhost:8000}"
ADMIN_URL="${ADMIN_URL:-http://localhost:80}"
ENV_FILE="${ENV_FILE:-.env.prod}"
SKIP_HTTPS="${SKIP_HTTPS:-false}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --verbose|-v) VERBOSE=true; shift ;;
        --domain) BASE_URL="https://$2"; API_URL="https://$2"; ADMIN_URL="https://$2"; shift 2 ;;
        --skip-https) SKIP_HTTPS=true; shift ;;
        --env-file) ENV_FILE="$2"; shift 2 ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo "  --verbose, -v     详细输出"
            echo "  --domain DOMAIN   指定验证域名 (自动使用 HTTPS)"
            echo "  --skip-https      跳过 HTTPS 验证"
            echo "  --env-file FILE   环境变量文件"
            exit 0
            ;;
        *) shift ;;
    esac
done

# ----------------------------------------------------------
# 工具函数
# ----------------------------------------------------------
check() {
    local name="$1"
    local result="$2"
    local detail="${3:-}"
    local critical="${4:-true}"

    if [[ "$result" -eq 0 ]]; then
        echo -e "  ${GREEN}[PASS]${NC} $name"
        ((PASS++))
        if [[ "$VERBOSE" == "true" ]] && [[ -n "$detail" ]]; then
            echo -e "          ${CYAN}→${NC} $detail"
        fi
    elif [[ "$critical" == "false" ]]; then
        echo -e "  ${YELLOW}[WARN]${NC} $name — $detail"
        ((WARN++))
    else
        echo -e "  ${RED}[FAIL]${NC} $name — $detail"
        ((FAIL++))
    fi
}

http_get() {
    local url="$1"
    local expected_code="${2:-200}"
    local retries="${3:-$MAX_RETRIES}"

    for i in $(seq 1 $((retries + 1))); do
        local resp
        resp=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" -k "$url" 2>/dev/null || echo "000")
        if [[ "$resp" == "$expected_code" ]]; then
            echo "$resp"
            return 0
        fi
        [[ $i -le $retries ]] && sleep 2
    done
    echo "$resp"
    return 1
}

http_get_json() {
    local url="$1"
    local retries="${2:-$MAX_RETRIES}"
    for i in $(seq 1 $((retries + 1))); do
        local resp
        resp=$(curl -s --max-time "$TIMEOUT" -k "$url" 2>/dev/null)
        if echo "$resp" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            echo "$resp"
            return 0
        fi
        [[ $i -le $retries ]] && sleep 2
    done
    echo "{}"
    return 1
}

# ----------------------------------------------------------
# 标题
# ----------------------------------------------------------
echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║      优丁建材 SaaS — 部署验证报告           ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"
echo "  验证时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  目标:     $BASE_URL"
echo ""

# ============================================================
# 1. 基础设施检查
# ============================================================
echo -e "${CYAN}═══ 1. 基础设施检查 ═══${NC}"

# Docker 运行状态
docker info &>/dev/null 2>&1
check "Docker 守护进程运行" $? "docker info" false

# 容器运行状态
CONTAINERS=("youding-nginx" "youding-backend" "youding-postgres" "youding-redis" "youding-minio")
for container in "${CONTAINERS[@]}"; do
    if docker ps -q --filter "name=${container}" 2>/dev/null | grep -q .; then
        STATUS=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "not found")
        UPTIME=$(docker inspect -f '{{.State.StartedAt}}' "$container" 2>/dev/null | cut -d'T' -f2 | cut -d'.' -f1)
        check "$container ($STATUS, since $UPTIME)" 0 ""
    else
        if [[ "$container" == "youding-minio" ]]; then
            check "$container" 1 "MinIO 未运行 (非必需服务)" false
        else
            check "$container" 1 "容器未运行" true
        fi
    fi
done

# 容器资源使用
echo ""
echo -e "${CYAN}  容器资源使用:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
    $(docker ps -q --filter "name=youding") 2>/dev/null || true

# ============================================================
# 2. 后端 API 健康检查
# ============================================================
echo ""
echo -e "${CYAN}═══ 2. 后端 API 检查 ═══${NC}"

# 基础健康
HTTP_CODE=$(http_get "$API_URL/health" 200 0)
check "GET /health → 200" $? "响应码: $HTTP_CODE"

# API v1 健康
HTTP_CODE=$(http_get "$API_URL/api/v1/health" 200 0)
check "GET /api/v1/health → 200" $? "响应码: $HTTP_CODE"

# 数据库连接检查
HTTP_CODE=$(http_get "$API_URL/api/v1/health/db" 200 0)
check "GET /api/v1/health/db → 200" $? "数据库连通" false

# 就绪检查
HTTP_CODE=$(http_get "$API_URL/api/v1/health/ready" 200 0)
check "GET /api/v1/health/ready → 200" $? "所有依赖就绪"

# API 文档
HTTP_CODE=$(http_get "$API_URL/docs" 200 0)
check "GET /docs (Swagger) → 200" $? "API 文档可访问"

# OpenAPI JSON
HTTP_CODE=$(http_get "$API_URL/openapi.json" 200 0)
check "GET /openapi.json → 200" $? "OpenAPI schema 可用" false

# ============================================================
# 3. 认证端点
# ============================================================
echo ""
echo -e "${CYAN}═══ 3. 认证端点检查 ═══${NC}"

# Login 端点存在
HTTP_CODE=$(http_get "$API_URL/api/v1/auth/login" 405)
check "POST /api/v1/auth/login (Method Not Allowed=405)" $? "预期 405 (GET → POST required)" false

HTTP_CODE=$(http_get "$API_URL/api/v1/auth/register" 405)
check "POST /api/v1/auth/register → 405" $? "预期 405" false

# ============================================================
# 4. 前端可访问性
# ============================================================
echo ""
echo -e "${CYAN}═══ 4. 前端访问检查 ═══${NC}"

# 主站
HTTP_CODE=$(http_get "$ADMIN_URL/" 200 0)
check "GET / (主站首页) → 200" $? "响应码: $HTTP_CODE"

# 静态资源
HTTP_CODE=$(http_get "$ADMIN_URL/favicon.ico" "200|304" 1)
check "GET /favicon.ico → 200/304" $? "静态资源可访问" false

HTTP_CODE=$(http_get "$ADMIN_URL/robots.txt" 200 1)
check "GET /robots.txt → 200" $? "robots.txt 可访问" false

# ============================================================
# 5. 数据库验证
# ============================================================
echo ""
echo -e "${CYAN}═══ 5. 数据库检查 ═══${NC}"

# 加载环境变量
set -a
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" || true
set +a

DB_USER="${DB_USER:-youding_admin}"
DB_NAME="${DB_NAME:-youding_prod}"
DB_PASSWORD="${DB_PASSWORD:-}"

if docker exec youding-postgres pg_isready -U "$DB_USER" -d "$DB_NAME" &>/dev/null; then
    check "PostgreSQL 连通性" 0 "pg_isready OK"

    # 表数量
    TABLE_COUNT=$(docker exec youding-postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
    if [[ -n "$TABLE_COUNT" ]] && [[ "$TABLE_COUNT" -gt 0 ]]; then
        check "数据库表数量: $TABLE_COUNT" 0 "Schema 已初始化"
    else
        check "数据库表数量" 1 "可能未运行迁移 (tables=$TABLE_COUNT)" false
    fi

    # 连接数
    DB_SIZE=$(docker exec youding-postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | tr -d ' ')
    echo -e "          ${CYAN}→${NC} 数据库大小: ${DB_SIZE:-未知}"
else
    check "PostgreSQL 连通性" 1 "pg_isready 失败"
fi

# ============================================================
# 6. Redis 验证
# ============================================================
echo ""
echo -e "${CYAN}═══ 6. Redis 检查 ═══${NC}"

REDIS_PASSWORD="${REDIS_PASSWORD:-}"

if docker exec youding-redis redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null | grep -q PONG; then
    check "Redis PING" 0 "PONG"

    KEYS=$(docker exec youding-redis redis-cli -a "${REDIS_PASSWORD}" DBSIZE 2>/dev/null | tr -d '\r\n ')
    MEM=$(docker exec youding-redis redis-cli -a "${REDIS_PASSWORD}" INFO memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d '\r\n ')
    echo -e "          ${CYAN}→${NC} 键数: ${KEYS:-0}, 内存: ${MEM:-N/A}"
else
    check "Redis PING" 1 "连接失败或密码错误"
fi

# ============================================================
# 7. Nginx / 安全头检查
# ============================================================
echo ""
echo -e "${CYAN}═══ 7. Nginx & 安全头检查 ═══${NC}"

# Nginx 健康
HTTP_CODE=$(http_get "$ADMIN_URL/healthz" 200 0)
check "GET /healthz → 200" $? "Nginx 健康端点"

# 安全头
for header_check in \
    "Strict-Transport-Security:HSTS" \
    "X-Frame-Options:SAMEORIGIN" \
    "X-Content-Type-Options:nosniff" \
    "Referrer-Policy:strict-origin-when-cross-origin"; do
    HEADER_NAME="${header_check%%:*}"
    HEADER_DESC="${header_check##*:}"

    ACTUAL=$(curl -sI --max-time 5 -k "$ADMIN_URL/" 2>/dev/null | grep -i "^$HEADER_NAME:" | head -1 | tr -d '\r\n' || echo "")
    if [[ -n "$ACTUAL" ]]; then
        check "$HEADER_DESC" 0 "$ACTUAL"
    else
        check "$HEADER_DESC" 1 "响应中未找到 $HEADER_NAME" false
    fi
done

# Gzip
GZIP=$(curl -sI --max-time 5 -k -H "Accept-Encoding: gzip" "$ADMIN_URL/" 2>/dev/null | grep -i "Content-Encoding" | tr -d '\r\n' || echo "")
if [[ "$GZIP" == *"gzip"* ]]; then
    check "Gzip 压缩已启用" 0 "$GZIP"
else
    check "Gzip 压缩" 1 "响应未压缩 (前端可能未通过 Nginx)" false
fi

# HTTPS 重定向
if [[ "$SKIP_HTTPS" != "true" ]]; then
    REDIRECT=$(curl -sI --max-time 5 -L -k "http://$ADMIN_URL/" 2>/dev/null | head -20 || echo "")
    if echo "$REDIRECT" | grep -qi "301\|https://"; then
        check "HTTP → HTTPS 重定向" 0 ""
    else
        check "HTTP → HTTPS 重定向" 1 "测试可能需要域名而非 localhost" false
    fi
fi

# ============================================================
# 8. API 功能冒烟测试
# ============================================================
echo ""
echo -e "${CYAN}═══ 8. API 冒烟测试 ═══${NC}"

# CORS 预检
HTTP_CODE=$(http_get "$API_URL/api/v1/health" 200 0)
check "API v1 响应正常" $? "status=$HTTP_CODE"

# 公开端点可访问 (不要求认证)
HTTP_CODE=$(http_get "$API_URL/api/v1/system/health" 200 0)
check "GET /api/v1/system/health → 200" $? "系统状态接口" false

# 验证返回 JSON 格式
RESP=$(curl -s --max-time "$TIMEOUT" "$API_URL/api/v1/health" 2>/dev/null || echo "")
if echo "$RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    check "API 返回 JSON 格式" 0 ""
else
    check "API 返回 JSON 格式" 1 "响应不是有效 JSON" false
fi

# ============================================================
# 9. TLS 证书检查
# ============================================================
echo ""
echo -e "${CYAN}═══ 9. TLS/SSL 证书检查 ═══${NC}"

if [[ "$SKIP_HTTPS" != "true" ]]; then
    # 提取主机名
    HOST_ONLY=$(echo "$ADMIN_URL" | sed -E 's|https?://||' | cut -d: -f1)

    if [[ "$HOST_ONLY" != "localhost" ]] && [[ "$HOST_ONLY" != "127.0.0.1" ]]; then
        CERT_INFO=$(echo | openssl s_client -servername "$HOST_ONLY" -connect "${HOST_ONLY}:443" 2>/dev/null | openssl x509 -noout -dates -subject 2>/dev/null || echo "")
        if [[ -n "$CERT_INFO" ]]; then
            check "SSL 证书存在" 0 "$(echo "$CERT_INFO" | head -2 | tr '\n' ' ')"
        else
            check "SSL 证书" 1 "无法连接到 ${HOST_ONLY}:443" false
        fi
    else
        # localhost 测试
        CERT_INFO=$(echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")
        if [[ -n "$CERT_INFO" ]]; then
            check "localhost SSL 证书" 0 "$(echo "$CERT_INFO" | head -1)"
        else
            check "localhost SSL" 1 "自签名证书正常" false
        fi
    fi
else
    echo -e "  ${YELLOW}[SKIP]${NC} HTTPS 验证已跳过"
fi

# ============================================================
# 10. MinIO 对象存储
# ============================================================
echo ""
echo -e "${CYAN}═══ 10. MinIO 对象存储 ═══${NC}"

# MinIO 健康检查
if docker exec youding-minio curl -sf http://localhost:9000/minio/health/live &>/dev/null; then
    check "MinIO 存活检查" 0 "minio/health/live OK"
else
    check "MinIO" 1 "MinIO 不可用" false
fi

# ============================================================
# 总结
# ============================================================
TOTAL=$((PASS + FAIL + WARN))

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  验证报告总结${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  总计:  $TOTAL 项检查"
echo -e "  ${GREEN}通过:  $PASS${NC}"
echo -e "  ${RED}失败:  $FAIL${NC}"
echo -e "  ${YELLOW}警告:  $WARN${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}  ✓ 所有关键检查通过 — 系统运行正常${NC}"
    exit 0
else
    echo -e "${RED}  ✗ 存在 $FAIL 项失败 — 请检查上述日志${NC}"
    echo ""
    echo "  常见修复:"
    echo "    1. 容器未运行 → docker compose -f docker-compose.prod.yml up -d"
    echo "    2. 数据库连接 → 检查 .env.prod 中的 DB_PASSWORD"
    echo "    3. Nginx 配置 → docker exec youding-nginx nginx -t"
    echo "    4. 查看日志 → docker compose logs -f backend"
    exit 1
fi

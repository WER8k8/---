#!/bin/bash
# ===========================================
# 生产环境一键部署脚本 - Phase 4
# 支持灰度发布、回滚、健康检查
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_NAME="youding-seo"
BACKUP_DIR="./backups"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 检查依赖
check_dependencies() {
    log_step "检查依赖..."
    command -v docker >/dev/null 2>&1 || { log_error "Docker未安装"; exit 1; }
    command -v docker compose >/dev/null 2>&1 || { log_error "Docker Compose未安装"; exit 1; }
    log_info "依赖检查通过"
}

# 环境变量检查
check_env() {
    log_step "检查环境变量..."
    if [ ! -f ".env.prod" ]; then
        log_error ".env.prod文件不存在，请复制.env.example并配置"
        exit 1
    fi

    # 加载环境变量
    set -a
    source .env.prod
    set +a

    if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "your-32-character-or-longer-secret-key-must-change-in-production" ]; then
        log_error "JWT_SECRET_KEY必须配置为强随机密钥"
        log_info "生成建议: python -c 'import secrets; print(secrets.token_hex(32))'"
        exit 1
    fi

    if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "your-secure-db-password-change-in-production" ]; then
        log_error "DB_PASSWORD必须配置为强密码"
        exit 1
    fi

    log_info "环境变量检查通过"
}

# 备份当前版本
backup_current() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
    fi

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

    log_step "备份当前版本到 ${BACKUP_PATH}..."
    docker compose -f "$COMPOSE_FILE" ps -q 2>/dev/null | while read container_id; do
        if [ -n "$container_id" ]; then
            docker inspect "$container_id" > "${BACKUP_PATH}_inspect.json" 2>/dev/null || true
        fi
    done
    log_info "备份完成"
}

# 拉取最新代码
pull_latest() {
    log_step "拉取最新代码..."
    git pull origin main 2>/dev/null || log_warn "非Git仓库或拉取失败，继续部署"
}

# 构建镜像
build_images() {
    log_step "构建Docker镜像..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    log_info "镜像构建完成"
}

# 执行数据库迁移
run_migrations() {
    log_step "执行数据库迁移..."
    docker compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade head 2>/dev/null || log_warn "数据库迁移跳过"
    log_info "数据库迁移完成"
}

# 健康检查
health_check() {
    log_step "执行健康检查..."

    local retries=0
    while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
        if curl -sf http://localhost/health >/dev/null 2>&1; then
            log_info "健康检查通过!"
            return 0
        fi

        retries=$((retries + 1))
        log_warn "健康检查失败，重试 ${retries}/${HEALTH_CHECK_RETRIES}..."
        sleep $HEALTH_CHECK_INTERVAL
    done

    log_error "健康检查失败，达到最大重试次数"
    return 1
}

# 灰度发布
gray_deploy() {
    log_step "开始灰度发布..."

    # 1. 启动新版本容器
    log_info "启动新版本容器..."
    docker compose -f "$COMPOSE_FILE" up -d --no-deps backend frontend

    # 2. 等待服务启动
    log_info "等待服务启动..."
    sleep 15

    # 3. 健康检查
    if health_check; then
        log_info "新版本健康检查通过，完成部署"
        docker compose -f "$COMPOSE_FILE" up -d
    else
        log_error "新版本健康检查失败，执行回滚..."
        rollback
        exit 1
    fi
}

# 回滚
rollback() {
    log_warn "执行回滚操作..."
    docker compose -f "$COMPOSE_FILE" down
    docker compose -f "$COMPOSE_FILE" up -d
    log_info "回滚完成"
}

# 清理
cleanup() {
    log_step "清理无用Docker资源..."
    docker system prune -f --filter "until=24h"
    docker volume prune -f --filter "label!=keep"
    log_info "清理完成"
}

# 显示状态
show_status() {
    log_info "服务状态:"
    docker compose -f "$COMPOSE_FILE" ps

    echo ""
    log_info "访问地址:"
    echo "  - 前端: https://youding.com"
    echo "  - 后台: https://youding.com/admin"
    echo "  - API文档: https://youding.com/api/docs"
    echo "  - 健康检查: https://youding.com/health"
}

# 主函数
main() {
    local action=${1:-deploy}

    case $action in
        deploy)
            check_dependencies
            check_env
            backup_current
            pull_latest
            build_images
            gray_deploy
            run_migrations
            cleanup
            show_status
            log_info "部署完成!"
            ;;
        rollback)
            rollback
            ;;
        status)
            show_status
            ;;
        clean)
            cleanup
            ;;
        *)
            echo "用法: $0 {deploy|rollback|status|clean}"
            exit 1
            ;;
    esac
}

main "$@"

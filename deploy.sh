#!/bin/bash
# ============================================
# 优丁建材 - 一键部署脚本
# 使用方法：bash deploy.sh
# ============================================

set -e

echo "========================================"
echo "优丁建材官网 - 自动化部署脚本"
echo "========================================"

# 检查必要工具
check_dependencies() {
    echo "🔍 检查依赖工具..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    echo "✅ 依赖检查通过"
}

# 配置环境
setup_environment() {
    echo ""
    echo "📝 配置环境..."
    
    if [ ! -f .env.prod ]; then
        echo "⚠️ 未找到.env.prod文件"
        echo "📋 正在从模板创建.env.prod..."
        cp .env.prod.example .env.prod
        echo ""
        echo "❌ 请先编辑.env.prod文件，填入真实配置后再运行部署"
        echo "📌 必填配置项："
        echo "   - DOMAIN (域名)"
        echo "   - DB_PASSWORD (数据库密码)"
        echo "   - JWT_SECRET_KEY (JWT密钥)"
        echo "   - AI_NVIDIA_API_KEY (英伟达API密钥)"
        echo "   - SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD (邮件服务)"
        echo ""
        echo "💡 编辑命令：vim .env.prod"
        exit 1
    fi
    
    # 加载环境变量
    source .env.prod
    
    # 验证必填配置
    if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "www.youdingjiancai.com" ]; then
        echo "❌ 请修改.env.prod中的DOMAIN为实际域名"
        exit 1
    fi
    
    if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "your-secure-db-password-change-me" ]; then
        echo "❌ 请修改.env.prod中的DB_PASSWORD为强密码"
        exit 1
    fi
    
    if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "your-jwt-secret-key-here-change-me" ]; then
        echo "❌ 请修改.env.prod中的JWT_SECRET_KEY"
        echo "💡 生成命令：python -c 'import secrets; print(secrets.token_hex(32))'"
        exit 1
    fi
    
    echo "✅ 环境配置检查通过"
}

# 构建镜像
build_images() {
    echo ""
    echo "🔨 构建Docker镜像..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml build --no-cache
    else
        docker compose -f docker-compose.prod.yml build --no-cache
    fi
    
    echo "✅ 镜像构建完成"
}

# 启动服务
start_services() {
    echo ""
    echo "🚀 启动服务..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml up -d
    else
        docker compose -f docker-compose.prod.yml up -d
    fi
    
    echo "✅ 服务已启动"
}

# 等待服务就绪
wait_for_services() {
    echo ""
    echo "⏳ 等待服务就绪..."
    
    # 等待PostgreSQL
    echo "  等待数据库启动..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U $DB_USER &> /dev/null; then
            echo "  ✅ 数据库已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "  ❌ 数据库启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 等待后端API
    echo "  等待后端API启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
            echo "  ✅ 后端API已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "  ⚠️ 后端API启动超时（可能正常，请手动检查）"
            break
        fi
        sleep 2
    done
}

# 运行数据库迁移
run_migrations() {
    echo ""
    echo "🗄️ 运行数据库迁移..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
    else
        docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
    fi
    
    echo "✅ 数据库迁移完成"
}

# 检查服务状态
check_status() {
    echo ""
    echo "📊 服务状态："
    echo "========================================"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml ps
    else
        docker compose -f docker-compose.prod.yml ps
    fi
    
    echo ""
    echo "========================================"
    echo "🌐 访问地址："
    echo "   前端：https://$DOMAIN"
    echo "   后端API：https://$DOMAIN/api/v1"
    echo "   API文档：https://$DOMAIN/api/docs"
    echo "   管理后台：https://$DOMAIN/admin"
    echo ""
    echo "📋 常用命令："
    echo "   查看日志：docker-compose -f docker-compose.prod.yml logs -f"
    echo "   停止服务：docker-compose -f docker-compose.prod.yml down"
    echo "   重启服务：docker-compose -f docker-compose.prod.yml restart"
    echo "   更新部署：bash deploy.sh"
    echo "========================================"
}

# 主流程
main() {
    check_dependencies
    setup_environment
    build_images
    start_services
    wait_for_services
    run_migrations
    check_status
    
    echo ""
    echo "🎉 部署完成！"
}

main

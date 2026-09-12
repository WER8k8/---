#!/bin/bash
# ==============================================
# 轻集料混凝土SEO系统 - 部署脚本
# ==============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=============================================="
echo "    轻集料混凝土SEO系统 - 部署脚本"
echo "==============================================${NC}"

# 检查参数
if [ $# -lt 1 ]; then
    echo -e "${RED}用法: $0 <环境> [版本]"
    echo "环境: dev | staging | prod"
    echo "版本: 可选，默认latest${NC}"
    exit 1
fi

ENV=$1
VERSION=${2:-latest}

echo -e "${YELLOW}部署环境: $ENV${NC}"
echo -e "${YELLOW}部署版本: $VERSION${NC}"

# 切换到项目目录
cd "$(dirname "$0")/.."

# 检查.env文件
if [ ! -f .env.${ENV} ]; then
    echo -e "${RED}错误: 未找到.env.${ENV}文件${NC}"
    exit 1
fi

# 复制环境配置
cp .env.${ENV} .env

# 拉取最新代码（如果有git）
if [ -d .git ]; then
    echo -e "${YELLOW}拉取最新代码...${NC}"
    git pull origin main
fi

# 停止现有服务
echo -e "${YELLOW}停止现有服务...${NC}"
docker-compose down

# 构建新镜像
echo -e "${YELLOW}构建Docker镜像...${NC}"
docker-compose build --no-cache

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 30

# 健康检查
echo -e "${YELLOW}执行健康检查...${NC}"
RESPONSE=$(curl -s http://localhost:8000/health)

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}部署成功!${NC}"
    echo -e "${BLUE}服务状态:${NC}"
    docker-compose ps
else
    echo -e "${RED}部署失败!${NC}"
    echo "响应: $RESPONSE"
    docker-compose logs backend
    exit 1
fi
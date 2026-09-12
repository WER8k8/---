#!/bin/bash
# ==============================================
# 轻集料混凝土SEO系统 - 一键启动脚本
# ==============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================="
echo "    轻集料混凝土SEO系统 - 一键启动脚本"
echo "==============================================${NC}"

# 检查是否存在.env文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: 未找到.env文件，将使用默认配置${NC}"
    cp .env.example .env
    echo -e "${GREEN}已创建.env文件，请根据需要修改配置${NC}"
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker服务未运行，请先启动Docker${NC}"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: docker-compose未安装${NC}"
    exit 1
fi

echo -e "${YELLOW}正在启动服务...${NC}"

# 创建必要的目录
mkdir -p uploads logs certbot/conf certbot/www

# 启动所有服务
docker-compose up -d

echo -e "${GREEN}服务启动中，请等待30秒后访问...${NC}"

# 显示服务状态
echo -e "\n${BLUE}服务状态:${NC}"
docker-compose ps

echo -e "\n${GREEN}启动完成!${NC}"
echo -e "${BLUE}访问地址:${NC}"
echo "  - API文档: http://localhost:8000/docs"
echo "  - 健康检查: http://localhost:8000/health"
echo "  - Nginx: http://localhost"
echo -e "\n${YELLOW}停止服务: ./scripts/stop.sh${NC}"
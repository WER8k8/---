#!/bin/bash
# ===========================================
# SSL证书自动申请脚本 - Let's Encrypt
# 使用 certbot 自动申请和配置SSL证书
# ===========================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 配置
DOMAIN=${1:-youding.com}
WWW_DOMAIN="www.${DOMAIN}"
SSL_DIR="./docker/nginx/ssl"
EMAIL="${2:-admin@${DOMAIN}}"

echo "=========================================="
echo "Let's Encrypt SSL证书自动申请脚本"
echo "=========================================="
echo "域名: ${DOMAIN}, ${WWW_DOMAIN}"
echo "邮箱: ${EMAIL}"
echo ""

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v certbot &> /dev/null; then
        log_warn "certbot未安装，正在安装..."

        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot python3-certbot-nginx
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot python3-certbot-nginx
        else
            log_error "无法自动安装certbot，请手动安装"
            exit 1
        fi
    fi

    log_info "依赖检查通过"
}

# 停止Nginx（standalone模式需要）
stop_nginx() {
    log_info "停止Nginx服务..."
    docker compose -f docker-compose.prod.yml down nginx 2>/dev/null || true
}

# 申请证书
request_certificate() {
    log_info "申请SSL证书..."

    # 创建SSL目录
    mkdir -p "${SSL_DIR}"

    # 使用standalone模式申请证书
    sudo certbot certonly \
        --standalone \
        --preferred-challenges http \
        -d "${DOMAIN}" \
        -d "${WWW_DOMAIN}" \
        --email "${EMAIL}" \
        --agree-tos \
        --non-interactive \
        --keep-until-expiring

    log_info "证书申请成功!"
}

# 复制证书到项目目录
copy_certificates() {
    log_info "复制证书到项目目录..."

    CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

    sudo cp "${CERT_DIR}/fullchain.pem" "${SSL_DIR}/fullchain.pem"
    sudo cp "${CERT_DIR}/privkey.pem" "${SSL_DIR}/privkey.pem"

    # 设置权限
    sudo chmod 644 "${SSL_DIR}/fullchain.pem"
    sudo chmod 600 "${SSL_DIR}/privkey.pem"

    log_info "证书已复制到 ${SSL_DIR}/"
}

# 启动Nginx
start_nginx() {
    log_info "启动Nginx服务..."
    docker compose -f docker-compose.prod.yml up -d nginx
}

# 配置自动续期
setup_auto_renewal() {
    log_info "配置证书自动续期..."

    # 创建续期脚本
    cat > "${SSL_DIR}/renew_cert.sh" << 'EOF'
#!/bin/bash
# SSL证书自动续期脚本

DOMAIN=${1:-youding.com}
SSL_DIR="./docker/nginx/ssl"

# 续期证书
sudo certbot renew --quiet

# 复制新证书到项目目录
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
sudo cp "${CERT_DIR}/fullchain.pem" "${SSL_DIR}/fullchain.pem"
sudo cp "${CERT_DIR}/privkey.pem" "${SSL_DIR}/privkey.pem"

# 重启Nginx
docker compose -f docker-compose.prod.yml restart nginx

echo "证书续期完成: $(date)"
EOF

    chmod +x "${SSL_DIR}/renew_cert.sh"

    # 添加到crontab（每月1号凌晨3点执行）
    (crontab -l 2>/dev/null; echo "0 3 1 * * cd $(pwd) && ${SSL_DIR}/renew_cert.sh ${DOMAIN}") | crontab -

    log_info "自动续期已配置（每月1号凌晨3点）"
}

# 验证证书
verify_certificate() {
    log_info "验证SSL证书..."

    if [ -f "${SSL_DIR}/fullchain.pem" ] && [ -f "${SSL_DIR}/privkey.pem" ]; then
        log_info "证书文件存在"

        # 显示证书信息
        openssl x509 -in "${SSL_DIR}/fullchain.pem" -noout -dates 2>/dev/null || true

        log_info "证书验证通过!"
        return 0
    else
        log_error "证书文件不存在"
        return 1
    fi
}

# 主函数
main() {
    check_dependencies
    stop_nginx
    request_certificate
    copy_certificates
    start_nginx
    setup_auto_renewal
    verify_certificate

    echo ""
    log_info "SSL证书配置完成!"
    echo ""
    echo "证书文件位置:"
    echo "  - ${SSL_DIR}/fullchain.pem"
    echo "  - ${SSL_DIR}/privkey.pem"
    echo ""
    echo "下一步:"
    echo "  1. 更新 docker-compose.prod.yml 中的Nginx配置"
    echo "  2. 重启服务: docker compose -f docker-compose.prod.yml restart nginx"
    echo "  3. 访问 https://${DOMAIN} 验证HTTPS是否正常"
}

# 执行
main

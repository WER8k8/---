#!/bin/bash
# Let's Encrypt证书自动续期脚本

DOMAIN="youding.com"
EMAIL="admin@youding.com"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

echo "🔐 开始申请/续期SSL证书..."

# 检查certbot是否安装
if ! command -v certbot &> /dev/null; then
    echo "❌ certbot未安装，正在安装..."
    apt-get update && apt-get install -y certbot python3-certbot-nginx
fi

# 申请证书（首次）
if [ ! -f "$CERT_PATH/fullchain.pem" ]; then
    echo "📝 首次申请证书..."
    certbot certonly --nginx \
        -d $DOMAIN \
        -d www.$DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --non-interactive \
        --keep-until-expiring
else
    echo "🔄 续期证书..."
    certbot renew --quiet
fi

# 检查证书续期结果
if [ $? -eq 0 ]; then
    echo "✅ 证书续期成功"
    echo "📅 证书有效期："
    openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -dates
    
    # 重新加载Nginx
    echo "🔄 重新加载Nginx..."
    nginx -s reload
else
    echo "❌ 证书续期失败，请检查日志"
    exit 1
fi

echo "🎉 SSL证书处理完成"

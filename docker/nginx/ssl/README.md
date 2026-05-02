# SSL证书配置说明

## Let's Encrypt 免费SSL证书申请

### 方法一：使用 certbot-auto（推荐）

```bash
# 1. 安装 certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 2. 申请证书（替换 yourdomain.com 为实际域名）
sudo certbot --nginx -d youding.com -d www.youding.com

# 3. 自动续期测试
sudo certbot renew --dry-run
```

### 方法二：手动申请

```bash
# 1. 停止 nginx
docker compose -f docker-compose.prod.yml down

# 2. 使用 standalone 模式申请
certbot certonly --standalone -d youding.com -d www.youding.com

# 3. 复制证书到项目目录
sudo cp /etc/letsencrypt/live/youding.com/fullchain.pem ./docker/nginx/ssl/fullchain.pem
sudo cp /etc/letsencrypt/live/youding.com/privkey.pem ./docker/nginx/ssl/privkey.pem

# 4. 启动服务
docker compose -f docker-compose.prod.yml up -d
```

## 证书文件说明

- `fullchain.pem` - 完整证书链（公钥+中间证书）
- `privkey.pem` - 私钥文件（务必妥善保管，不要提交到Git）

## 自动续期

Let's Encrypt证书有效期为90天，建议设置自动续期：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每月1号凌晨3点检查续期）
0 3 1 * * certbot renew --quiet && docker compose -f /path/to/docker-compose.prod.yml restart nginx
```

## 生产环境部署检查清单

- [ ] 证书已申请并放置在 `docker/nginx/ssl/` 目录
- [ ] `.gitignore` 已包含 `*.pem` 规则
- [ ] nginx配置已启用HTTPS
- [ ] HTTP自动跳转到HTTPS
- [ ] HSTS头部已配置
- [ ] 证书自动续期已设置

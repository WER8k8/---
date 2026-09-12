# 租户独立域 SSL 自动签发（C-05）

## 推荐方案

生产使用 **Caddy** 或 **Traefik** 做反向代理 + **ACME HTTP-01** 自动证书。

## Caddy 示例

```caddyfile
*.youding-saas.com {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy nuxt:3000
}

# 租户自定义域：按 Host 透传至同一 Nuxt，由 tenant.global.ts 解析
:443 {
    tls {
        on_demand
    }
    reverse_proxy nuxt:3000
}
```

## 验收

1. 租户在后台绑定 `www.xxxx.com` 并完成 DNS CNAME  
2. 访问 `https://www.xxxx.com` 证书有效  
3. 未知 Host 返回 404  

## 代码侧

- 域名绑定：`/api/v1/domains`  
- Host 解析：`/api/v1/domains/resolve?host=`  
- 前端：`frontend/middleware/tenant.global.ts`
- **Sprint O**：`SSL_PROVIDER=acme|certbot` + `ACME_WEBHOOK_URL`（见 `docs/Sprint-O-商用收尾.md`）

# 视频 → 租户官网流量（SEO / GEO）

> 业务目标：视频上传到视频网站 + 在租户官网落地，带来搜索曝光与询盘。

## 闭环

```text
AI 生成视频 → 酷播/R2 上云
       │
       ├─► 视频网站（YouTube 等）描述里带「官网链接 + 要点」
       │
       └─► 租户官网「视频中心」+ /v/{id} 落地页
              ├─ VideoObject JSON-LD（独立，不污染文章页）
              ├─ geo_facts（AI/GEO 可引用要点）
              ├─ videos-sitemap.xml
              └─ #contact 询盘 CTA（带 UTM）
```

## 关键 API

| 接口 | 说明 |
|------|------|
| `POST /media-factory/tasks/{id}/publish-traffic` | **推荐**：官网落地 + 可选 `platform_ids` |
| `POST /media-factory/tasks/{id}/publish-to-site` | 仅官网 |
| `GET /public/tenants/{domain}/videos` | 租户站视频列表 |
| `GET /public/tenants/{domain}/videos/{task_id}` | 单页 SEO 数据 |
| `GET /public/tenants/{domain}/videos-sitemap.xml` | 视频 sitemap |
| `POST /seo-matrix/publish` + `media_render_task_id` | 矩阵一键（默认 `publish_traffic=true`） |

## 配置

- `MEDIA_AUTO_PUBLISH_TENANT_SITE=true`：上云后自动登记官网视频页
- 任务需有 `tenant_id`（登录租户或注册绑定 `guest_token`）

## 与县域 SEO 文章的关系

- 矩阵**文章**仍走原有关键词/页面逻辑。
- **视频**使用 `resource_type=media_video` 的 `seo_metadata`，不写入文章 `schema_markup`。

# 多媒体工厂 · 视频云存储决策说明（PM / 技术评审用）

> **决策人**：工程侧（按业务目标与现有代码拍板）  
> **日期**：2026-05-31  
> **状态**：已定稿，可评审；有异议请在评审会上提出，再开 ADR 修订  
> **关联**：[MEDIA-FACTORY-CLOUD-STORAGE.md](./MEDIA-FACTORY-CLOUD-STORAGE.md)（实施细节）

---

## 一、给产品经理（1 分钟版）

**我们要解决什么**

- 视频渲染完成后：客户能**马上预览**（不卡接口），国内访问尽量**秒开**，海外能**稳定发到 YouTube 等平台**。
- 不把视频发布绑到 Obsidian 等笔记工具（封号/合规风险）。

**最终选型（已拍板）**

| 用途 | 方案 | 为什么 |
|------|------|--------|
| 国内播放 / 后台预览 | **酷播云（保利威点播）** | 官方 API 已接入；带点播转码与播放能力，适合「成品视频」 |
| 海外发布 + 长期归档 | **Cloudflare R2** | 出站流量政策友好、S3 标准、与现有海外 Egress 发布模型一致 |
| 灾备（可选） | **棱束链** | 上传失败时的备份直链，非默认播放源 |
| 开发 / 站内附件 | **现有 MinIO** | 项目里已有，**不**作为面向客户的国内 CDN |

**不采用的豆包方案**

- 腾讯云 CloudBase（豆包示例代码不可直接用，产品与酷播不同类）
- MinIO 当国内主 CDN（缺 CDN/域名时达不到「客户秒开」）
- 单独新建 `/api/video/upload` 与现有「渲染任务 → 自动上云」重复

**产品需要配合的事**

1. 在酷播 / Cloudflare 控制台开通账号，把密钥交给运维填入服务器 `.env`（不进 git）。
2. 上线前在控制台核对**免费额度、流量、存储**（以厂商当期政策为准，不写死「50GB」等营销数字）。
3. 内容合规：点播平台对违规内容会处理账号，与「换哪家云」无关，需保留用户协议与审核流程。

---

## 二、给技术团队（架构与落地）

### 2.1 架构图

```text
[用户] → 管理后台 / API
           │
           ▼
    创建 MediaRenderTask → 后台渲染（可先 Mock）
           │
           ├─► 本地 uploads/media_factory/{id}.mp4  （立刻 preview，不挡请求）
           │
           └─► 守护线程并行上云（已实现）
                 ├─► 酷播  → cloud_vid, cloud_play_url     （国内优先播放）
                 └─► R2    → cloud_r2_key, cloud_r2_url   （海外 publish_video_url）

播放优先级：cloud_play_url（酷播）> R2 签名 URL > 本地 result_url
海外发布：publish_video_url → publish_service / YouTube 等拉源
出口 IP：Egress(global) / V2Ray — 只解决「调海外平台 API」，不存视频
```

### 2.2 代码落点（已实现 P1/P2 主体）

| 模块 | 路径 |
|------|------|
| 酷播上传 | `backend/app/services/media_cuplayer_service.py` |
| R2 上传 | `backend/app/services/media_r2_service.py` |
| 并行上云 + 播放 URL | `backend/app/services/media_cloud_upload_service.py` |
| 渲染完成后触发 | `backend/app/services/media_render_worker.py` |
| 任务序列化（含 cloud_*） | `backend/app/services/media_factory_service.py` |
| 表字段 + 开发库自动补列 | `backend/app/models/media_factory.py`、`app/db/session.py` |

### 2.3 豆包三方案技术结论（存档，避免以后再讨论）

| 方案 | 结论 | 备注 |
|------|------|------|
| 腾讯云 CloudBase | **不采纳为 L1** | 豆包 `tcb.TcbService` 片段不可靠；若未来要用应走 **COS 官方 SDK**，单独 POC |
| MinIO 自建 | **仅站内/开发** | 已有 `minio_service.py`；生产 C 端需 CDN+HTTPS，不重复建设 |
| 七牛云 | **P5 备选** | 仅当酷播额度/成本/合同不满足时，新增 `media_qiniu_service` 挂到同一 `sync_cloud_upload` |

### 2.4 配置清单（运维）

见 `backend/config/dev/.env.example` 中 `MEDIA_CUPLAYER_*`、`MEDIA_R2_*`。  
生产密钥只在服务器 `deploy/production` 环境变量，**禁止**提交仓库。

### 2.5 待办（按优先级）

| 优先级 | 事项 | 负责建议 | 状态 |
|--------|------|----------|------|
| P0 | 生产/测试环境填入酷播 + R2 密钥并跑通一条真实渲染 | 运维 + 后端 | 待做 |
| P0 | `guest_token` 注册绑定 API（未登录生成 → 注册归属租户） | 后端 | **已做** |
| P1 | 海外发布 + SEO 包（`/media-factory/tasks/{id}/publish`、`seo-bundle`、矩阵 `media_render_task_id`） | 后端 | **已做** |
| P2 | 棱束链备份上传 + 失败重试 | 后端 | 可选 |
| P5 | 七牛作为 L1 可配置备选 | 后端 | **不做除非 PM 提需求** |

---

## 三、评审会可讨论的问题（请 PM / 技术勾选）

- [ ] 酷播免费档是否满足前 3 个月业务量？不够则评估七牛或酷播付费档。
- [ ] R2 Bucket 是否绑定自定义域名 / `MEDIA_R2_CDN_BASE_URL`？
- [ ] 成品保留 72h + handoff 删文件策略是否与商务承诺一致？
- [ ] 是否需要「仅国内租户 / 仅海外租户」分流存储（当前：同一任务双写酷播+R2）？

---

## 四、决策记录（ADR 摘要）

**背景**：豆包提供 CloudBase / MinIO / 七牛三套通用 Demo，与已定双轨方案冲突。  
**决定**：维持 **酷播（L1 国内）+ R2（L2 海外）+ 棱束链（L3 可选）**；MinIO 限站内；七牛暂不实现，列为 P5 备选。  
**后果**：需运营开通两家云账号；工程不再接第三套独立上传 API。  
**不决定的事**：具体每月费用以厂商账单为准，由 PM 与财务跟进。

---

## 五、验证清单（技术自测）

```powershell
# 本地
powershell -File scripts/start-dev-admin.ps1
# 登录 admin / admin123
# 文章转视频或媒体工厂：提交渲染 → 任务 done → cloud_upload_status 变为 done/partial/skipped
# GET /api/v1/media-factory/tasks/{id} 中 preview_url、publish_video_url 符合预期
```

未配置云密钥时：`cloud_upload_status=skipped`，仍可用本地 `preview_url`，**不影响演示**。

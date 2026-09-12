# 多媒体工厂 · 视频云存储方案（整合版）

> 更新：2026-05-31  
> **不采用 Obsidian** 作为发布链路（封号/异常风险高）；发布统一走 **管理后台 + 多平台发布 API**。

---

## 一、目标

1. 渲染完成后：**服务器暂存** → **异步上云** → 登记可播放/可下载地址。  
2. 客户**注册/登录**后，历史视频按 `guest_token` 或 `tenant_id` **自动归属**。  
3. 国内访问 **秒开、无广告**；成本可控（免费额度 + 大容量备份）。

---

## 二、国内 / 国外双轨（已定稿）

| 场景 | 存储与播放 | 发布出口 |
|------|------------|----------|
| **国内**（官网预览、国内平台） | **酷播云** L1：5GB + 月流量，无广告、秒开 | 国内平台 + `cn` 区域 **Egress IP 槽位** |
| **国外**（YouTube / TikTok / Meta 等） | **Cloudflare R2** L2：约 10GB 免费、**出站流量免费**、S3 API、可商用 | **global** 区域 Egress + 可选 **V2RayN**（`/admin/v2ray`） |

说明：

- **R2 管「视频放哪、国外平台从哪拉文件」**——全球可访问的 `video_url`（预签名或自定义域名）。  
- **VPN / Egress 管「服务器访问国外平台 API」**——不是把视频存在 VPN 里；发布任务走 `egress_endpoints`（见 `seo-matrix/publish.vue` 海外平台 + 指纹隔离）。  
- 二者配合：渲染完成 → 上传 R2 → 发布时 `YouTubePublisher` 等用 `content.video_url` 拉取（见 `publish_service.py`）。

**R2 用于国外发布的理由（采用）**

- 永久免费额度内 10GB 存储，出站免流量费（以 Cloudflare 当前政策为准）。  
- S3 兼容，`boto3` 易接 Celery 异步上传。  
- 海外平台拉流稳定，不依赖国内酷播 CDN。  
- 与系统已有 **global 平台 + Egress** 模型一致。

## 三、三层存储分工（技术栈）

| 层级 | 方案 | 额度（公开宣传） | 角色 | 说明 |
|------|------|------------------|------|------|
| **L1 国内播放** | [酷播云](https://www.cuplayer.com/cloud/)（保利威点播） | 约 5GB + 50GB/月流量 | 国内预览 / 转码 / 嵌入 | 官方 `v.polyv.net` 上传接口 |
| **L2 国外 + 归档** | Cloudflare **R2** | 约 10GB 免费 + 出站免费 | **海外发布主源**、长期归档 | `MEDIA_R2_*` 配置；路径 `tenants/{tenant_id}/videos/{id}.mp4` |
| **L3 备选** | **棱束链**（S3 兼容） | 约 50GB 免费 | 灾备直链 | R2/酷播失败时兜底 |

**原则**

- **国内播放**：酷播 `mp4` / `hls` / iframe。  
- **国外发布**：R2 预签名 URL（或 `MEDIA_R2_CDN_BASE_URL`）写入 `video_url` 再发到 YouTube 等。  
- **权威副本**：以 R2 为准；酷播为国内加速层。  
- **备份**：棱束链可选。

---

## 四、流水线（无 Obsidian）

```text
[MoneyPrinter 生成] → 本地 uploads/media_factory/{id}.mp4
        │
        ├─► Celery: upload_r2          → cloud_r2_key, cloud_r2_url (签名)
        ├─► Celery: upload_cuplayer    → cloud_vid, cloud_play_url (酷播)
        └─► Celery: upload_lenslink    → cloud_backup_url (可选/失败重试)
        │
        ▼
  media_render_tasks 更新 + expires_at / handoff 照旧
        │
        ├─► 管理后台：预览 / 下载 / 登记 handoff
        ├─► 国内发布 / 预览：cloud_play_url（酷播）
        └─► 国外发布：cloud_r2_url → Egress(global) / V2Ray → YouTube/TikTok/…
```

与现有代码对齐：

- 本地暂存、TTL、`handoff`：见 `media_retention_service.py`。  
- 任务表 `tenant_id`：见 `MediaRenderTask`；需新增字段见下文。  
- 发布：走现有 **SEO 矩阵 / unified_publish**，不经过 Obsidian。

---

## 五、注册绑定（guest → 租户）

| 阶段 | 字段 | 行为 |
|------|------|------|
| 未登录生成 | `guest_token`（UUID，Cookie） | 任务写入 `guest_token`，`tenant_id` 为空 |
| 注册成功 | 创建 `User` + `UserTenant` | 批量 `UPDATE`：`guest_token` 匹配 → `tenant_id` |
| 已登录租户 | `resolve_tenant_id_for_user` | 与现逻辑一致 |

云路径迁移（可选 P2）：`guest/xxx/` → `tenants/{tenant_id}/` 对象 rename。

---

## 六、酷播云接入要点（已审校豆包方案）

### 6.1 豆包方案：哪些采用、哪些修正

| 豆包说法 | 结论 | 说明 |
|----------|------|------|
| 5GB + 50GB 流量、无广告、可 API | ✅ 采用（额度以控制台为准） | 与选型一致，上线前在后台核对当前政策 |
| v4 注册/登录地址 | ✅ 采用 | https://v.cuplayer.com/v4/#/register 、#/login |
| 拿 writetoken + 密钥 | ✅ 采用 | 官方路径：**设置 → API 接口**（或 v4 开发者中心）；见下表 |
| 流程：暂存 → 上传 → 播放 | ✅ 采用 | 与本文第三节一致 |
| `https://api.cuplayer.com/v1/video/upload` | ❌ **不采用** | **官方文档无此地址**；勿照抄 |
| 豆包 PHP 示例整段复制 | ❌ **不采用** | 端点错误；本项目用 **Python/FastAPI** |
| 「每客户自动酷播子账号」 | ⚠️ 修正 | 官方 API 是 **cataid 分类目录**，不是多子账号；租户隔离用「每租户一个 cataid」或标题前缀 |
| iframe 嵌入播放 | ✅ 采用 | 后台预览 / 官网嵌入 |
| 7 天删旧视频省空间 | ✅ 采用 | 与 `MEDIA_RETENTION_HOURS` + 酷播删除 API 对齐 |
| 棱束链 50GB 备选 | ✅ 采用 | 见第七节；注册地址以官网为准 |

### 6.2 官方密钥（与 `.env` 映射）

| 酷播控制台 | 环境变量 | 用途 |
|------------|----------|------|
| userid | `MEDIA_CUPLAYER_USERID` | 部分接口、播放器 |
| writetoken | `MEDIA_CUPLAYER_WRITETOKEN` | **上传** |
| readtoken | （可选） | 读视频列表 |
| secretkey | `MEDIA_CUPLAYER_SECRETKEY` | 开启签名时 `sign=sha1(...)` |

豆包写的「API Key + Secret」在 v4 界面可能等同 **writetoken + secretkey**，以控制台实际字段名为准。

### 6.3 开通步骤（照做即可）

1. 注册：https://v.cuplayer.com/v4/#/register  
2. 登录：https://v.cuplayer.com/v4/#/login  
3. **设置 → API 接口**（或开发者中心）复制 userid / writetoken / secretkey。  
4. **视频分类管理** 为每个租户建分类，记下 **cataid**（或先用根目录 `cataid=1`）。  
5. 填入 `backend/config/dev/.env`（勿提交 git）。

### 6.4 上传接口（以官方为准）

- 文档：[服务器 API](http://b.cuplayer.com/cloud/doc/server/11273473.html)、[上传视频](https://www.cuplayer.com/cloud/doc/server/11293476.html)  
- **正确 URL**：`POST http://v.polyv.net/uc/services/rest?method=uploadfile`  
- 表单字段：`writetoken`、`JSONRPC`（`{"title","tag","desc"}`）、`Filedata`（mp4 等）、`cataid`（可选）  
- 若后台开启签名：`sign = sha1('cataid=' + cataid + '&JSONRPC=' + JSONRPC + '&writetoken=' + writetoken + secretkey)`  
- 返回：`vid`、`mp4` / `hls`、`first_image` → 存 `cloud_vid`、`cloud_play_url`  
- **POST 不要带 Cookie**（官方注意事项）

### 6.5 本项目实现方式（非 PHP）

在 `backend` 用 **httpx + Celery** 上传，渲染完成触发 `upload_cuplayer` 任务；**不需要**豆包里的 PHP，也**不需要**单独要 Node 版——除非你要在纯 Node 边缘脚本里上传（可选附录）。

### 6.6 播放嵌入

```html
<!-- src 使用上传返回的播放器/iframe 地址，或管理后台生成的调用代码 -->
<iframe src="（酷播返回的播放页）" width="100%" height="600" frameborder="0" allowfullscreen></iframe>
```

管理后台 `VideoPlayer` 组件优先播 `cloud_play_url`（mp4/hls），无则回退本地 `result_url`。

### 6.7 注意

酷播是 **点播转码平台**，不是通用 OSS；**大文件归档仍走 R2**，酷播负责国内播放体验。

---

## 七、R2（国外发布主源）

### 7.1 开通（Cloudflare 控制台）

1. 创建 R2 Bucket（如 `youding-media-prod`）。  
2. 创建 **R2 API Token**（Object Read & Write）。  
3. 记下：`account_id`、`access_key_id`、`secret_access_key`。  
4. （可选）绑定自定义域名或 `pub-xxx.r2.dev` 公共访问；海外发布建议 **预签名 URL**（有时效，更安全）。

### 7.2 接入本项目

- 环境变量：`MEDIA_R2_*`（见 `backend/config/dev/.env.example`）。  
- 上传端点：`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`（S3 兼容）。  
- 渲染完成后 Celery 上传 → `cloud_r2_key`、`cloud_r2_url`。  
- **海外发布**：`publish` 任务 `video_url` = R2 签名 URL；Worker 经 **global Egress** 访问 YouTube API 并拉取该 URL。

### 7.3 与 VPN / Egress 的关系

```text
视频文件 ──上传──► R2（全球可读 URL）
                      ▲
发布 Worker ──Egress(global) / V2Ray──► YouTube、TikTok API
              （解决「国内服务器访问不了国外平台」，不是存视频）
```

- 管理端：**统一发布** → 海外平台选 **global 静态 IP + 指纹**（`publish.vue`）。  
- **V2RayN**：` /admin/v2ray` 为运维/备用出口，与 R2 存储解耦。

### 7.4 国内如需 R2 加速（可选）

R2 自定义域名 + 国内 CDN 回源（又拍/七牛等），仅当国内也要直连 R2 时配置 `MEDIA_R2_CDN_BASE_URL`。

---

## 八、棱束链（备选）

- 控制台：个人中心 → API → 开启后获取 SecretID/SecretKey。  
- 直链空间：创建分享即直链；支持 S3 兼容策略（以控制台文档为准）。  
- 用途：R2/酷播上传失败重试；或仅存备份 URL，不对外默认展示。

---

## 九、数据表扩展（建议迁移）

在 `media_render_tasks` 增加：

| 字段 | 说明 |
|------|------|
| `guest_token` | 注册前归属 |
| `cloud_provider` | `cuplayer` / `r2` / `lenslink` |
| `cloud_vid` | 酷播视频 ID |
| `cloud_play_url` | 默认播放地址（酷播 mp4/hls） |
| `cloud_r2_key` | R2 对象键 |
| `cloud_r2_url` | 最近签名 URL（可过期，不持久依赖） |
| `cloud_backup_url` | 棱束链直链 |
| `cloud_upload_status` | `pending` / `partial` / `done` / `failed` |

---

## 十、配置项（`.env`，勿提交密钥）

```env
# 存储策略：primary=对外播放优先，archive=归档优先
MEDIA_CLOUD_PLAY_PRIMARY=cuplayer
MEDIA_CLOUD_ARCHIVE=r2
MEDIA_CLOUD_BACKUP=lenslink

# 酷播云（保利威）— 设置→API 接口 获取
MEDIA_CUPLAYER_WRITETOKEN=
MEDIA_CUPLAYER_SECRETKEY=
MEDIA_CUPLAYER_USERID=
MEDIA_CUPLAYER_READTOKEN=
MEDIA_CUPLAYER_CATAID=1
# 上传端点（一般勿改）
MEDIA_CUPLAYER_UPLOAD_URL=http://v.polyv.net/uc/services/rest?method=uploadfile

# Cloudflare R2
MEDIA_R2_ACCOUNT_ID=
MEDIA_R2_ACCESS_KEY_ID=
MEDIA_R2_SECRET_ACCESS_KEY=
MEDIA_R2_BUCKET=
MEDIA_R2_PUBLIC_BASE_URL=
MEDIA_R2_CDN_BASE_URL=

# 棱束链（S3 兼容，以控制台为准）
MEDIA_LENSLINK_ENDPOINT=
MEDIA_LENSLINK_ACCESS_KEY=
MEDIA_LENSLINK_SECRET_KEY=
MEDIA_LENSLINK_BUCKET=
```

---

## 十一、实施顺序

> **团队决策说明（PM/技术评审）**：[MEDIA-FACTORY-STORAGE-DECISION.md](./MEDIA-FACTORY-STORAGE-DECISION.md)  
> 豆包 CloudBase / MinIO 主 CDN / 七牛替换方案：**不采纳**；七牛仅列 P5 备选。

| 阶段 | 内容 | 产出 | 状态 |
|------|------|------|------|
| **P0** | DB 字段 + `guest_token` 注册绑定 API | 迁移脚本 | 字段已加，绑定 API 待做 |
| **P1** | **R2 上传** + 签名 URL；海外发布 `video_url` 走 R2 | 国外视频可发 | 代码已接，待配密钥 |
| **P2** | 酷播官方接口上传；国内预览 | 国内秒开 | 代码已接，待配密钥 |
| **P3** | 发布任务绑定 global Egress（已有 UI，打通 media_factory） | 海外平台闭环 | 待做 |
| **P4** | 棱束链备份 + 失败重试 | 高可用 | 可选 |
| **P5** | 七牛作 L1 备选（仅当酷播不满足时） | 配置开关 | **不做，除非产品提需求** |

---

## 十二、与 Obsidian 的边界

| 用途 | 建议 |
|------|------|
| 产品文档、交接笔记 | 继续用桌面 `出海计` 知识库（只读同步 `docs/`） |
| 视频生成、上云、发布 | **仅平台内**（API + 管理后台） |
| 第三方笔记/脚本批量发视频 | **不做**，避免平台封号风险 |

---

## 十三、参考

- 现有保留策略：`backend/app/services/media_retention_service.py`  
- 目标架构 R2：`docs/adr/架构设计-2026-目标架构与性能.md`  
- 本地开发：`scripts/start-dev-admin.ps1`，`MEDIA_RETENTION_HOURS=72`

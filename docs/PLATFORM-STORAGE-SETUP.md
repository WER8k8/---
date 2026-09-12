# 平台产品图存储开通指南（运维一次性）

> **客户不需要注册七牛。** 租户在「产品图片空间」直接上传；平台运维在本指南完成后，全站国内租户走七牛、海外租户走 R2。

## 谁做什么

| 角色 | 七牛 / R2 | 酷播长视频 | 抖音 / 微信等 |
|------|-----------|------------|---------------|
| **平台运维（您）** | 注册、实名、配 `QINIU_*` / `MEDIA_R2_*` | — | — |
| **租户客户** | 无 | 自备酷播账号 | 后台 OAuth 绑定 |

## 一、七牛（国内产品图）— 必须人工的步骤

以下步骤因实名与法律要求 **无法代码代填**，只能您本人操作一次：

1. **注册**  
   https://portal.qiniu.com/signup  
   使用平台企业邮箱，勿用客户身份。

2. **实名认证**  
   https://portal.qiniu.com/user/profile  
   企业建议走企业认证；未完成则无法创建 Bucket / 上传。

3. **创建 Bucket**  
   https://portal.qiniu.com/kodo/bucket  
   - 区域选离服务器近的（如华东）  
   - 访问控制：公开读（产品图需 CDN 外链）  
   - 记录 **Bucket 名称** → `QINIU_BUCKET`

4. **绑定 CDN 域名（HTTPS）**  
   在 Bucket 或 CDN 控制台绑定形如 `https://img.yourdomain.com` 的域名，并完成 CNAME / 证书。  
   → `QINIU_PUBLIC_BASE_URL=https://img.yourdomain.com`

5. **创建 AK/SK**  
   https://portal.qiniu.com/user/key  
   → `QINIU_ACCESS_KEY` / `QINIU_SECRET_KEY`

## 二、自动化部分（验密钥 + 写服务器）

实名与 Bucket 建好后，用仓库脚本 **自动探测上传/删除**，通过后才写入 `.env`，避免配错：

```powershell
cd C:\Users\97907\Desktop\上线网站
powershell -File scripts/setup-platform-storage.ps1
```

按提示粘贴 AK/SK、Bucket、CDN 域名。脚本会：

1. 上传 1×1 探测图到 `_platform-probe/` 并删除  
2. 失败则 **不写入** env  
3. 成功则合并到 `backend/config/dev/.env`（或 `-EnvFile` 指定路径）

### 生产服务器

```powershell
# 本地验完密钥后，合并到远程 .env.prod（需 DEPLOY_HOST 或 -RemoteHost）
$env:DEPLOY_HOST = "root@your-server-ip"
powershell -File scripts/setup-platform-storage.ps1 `
  -EnvFile deploy\production\.env.prod `
  -RemoteHost $env:DEPLOY_HOST `
  -RemoteEnvPath /opt/youding/.env.prod
```

远程合并后 SSH 重启 backend：

```bash
cd /opt/youding && docker compose restart backend
```

### 仅探测（不写文件）

```powershell
$env:QINIU_ACCESS_KEY="..."
$env:QINIU_SECRET_KEY="..."
$env:QINIU_BUCKET="..."
$env:QINIU_PUBLIC_BASE_URL="https://img.example.com"
python scripts/probe-platform-storage.py --target qiniu
```

## 三、超管后台验收

登录超管 → **系统 → 存储开通**（`/admin/system/storage-provision`）：

- 查看七牛 / R2 是否已配置  
- **验收当前配置**：对运行中 env 再做上传探测  
- **试填密钥验收**：配服务器前先验 AK/SK（不落库）  
- 复制 env 片段到生产（勿提交 git）

API（需超管 Token）：

- `GET /api/v1/super-admin/storage-provision/status`
- `GET /api/v1/super-admin/storage-provision/checklist`
- `POST /api/v1/super-admin/storage-provision/verify-current`
- `POST /api/v1/super-admin/storage-provision/verify`

## 四、环境变量清单

```env
FILE_STORAGE_DEFAULT_REGION=cn
QINIU_ACCESS_KEY=
QINIU_SECRET_KEY=
QINIU_BUCKET=
QINIU_PUBLIC_BASE_URL=
QINIU_UPLOAD_HOST=https://upload.qiniup.com

# 海外（与视频工厂共用）
MEDIA_R2_ACCOUNT_ID=
MEDIA_R2_ACCESS_KEY_ID=
MEDIA_R2_SECRET_ACCESS_KEY=
MEDIA_R2_BUCKET=
MEDIA_R2_PUBLIC_BASE_URL=
```

模板：`deploy/production/env.template`、`backend/config/dev/.env.example`

## 五、生产告警

若 `ENVIRONMENT=production` 且默认分区（`FILE_STORAGE_DEFAULT_REGION=cn`）未配 `QINIU_*`，backend 启动日志会输出 **存储告警**，产品图会落本地磁盘（重启可能丢文件）。

## 六、常见问题

| 现象 | 处理 |
|------|------|
| 上传 HTTP 401/403 | 检查 AK/SK、Bucket 名、是否已实名 |
| 上传成功但外链 404 | `QINIU_PUBLIC_BASE_URL` 与 CDN 域名不一致或未 HTTPS |
| 客户问要不要开七牛 | 答复：**不需要**，平台已代开，直接上传即可 |
| 只想先上国内 | 只配 `QINIU_*`，`FILE_STORAGE_DEFAULT_REGION=cn` |

## 七、与开户流程的关系

租户注册向导中的「七牛云 · 产品图片空间」卡片标记为 **平台代开**（`owner: platform`），步骤里写「【平台运维】…」——客户侧动作为 **none**。  
平台完成本指南后，该卡片在运维视角可视为已就绪；租户侧仅使用「产品图片空间」上传。

---

相关代码：`backend/app/services/platform_storage_provision_service.py`  
相关脚本：`scripts/setup-platform-storage.ps1`、`scripts/probe-platform-storage.py`

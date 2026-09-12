# P0 + P1 修复规划（56 项问题）

> 基于本月代码深度扫描报告 | 规划日期：2026-07-20

---

## 修复依赖关系

```
P0-5 (路由注册) ──→ P0-7 (ScoreRadar) ──→ P1-1 (scoreBreakdown 类型)
    │
P0-6 (XSS) ──→ P0-8 (VariableIcon)
    │
P0-1 (API Key 明文) ──→ P0-4 (tenant AI config Key 读取)
    │
P0-2 (send_raw) ──→ P0-3 (追踪像素安全)
    │
P1-2 (search_leads) ──→ P1-3 (generate_outreach_email)
    │
P1-4 (租户隔离) ──→ P1-5 (草稿隔离)
    │
P1-6 (竞态) ──→ P1-7 (授权码碰撞) ──→ P1-8 (confirm_order 竞态)
```

---

## P0 修复方案（8 项，全部必须）

### P0-1：API Key 明文存储
**文件**：`backend/app/models/ai_config.py:48`
**现状**：`AIModelProvider.api_key = Column(String(255))` 明文
**修复**：
```python
# 引入已有的加密工具
from app.core.field_crypto import encrypt_field, decrypt_field

# 模型字段改名
api_key_encrypted = Column("api_key", String(500), nullable=False)  # 保持列名兼容

# 读取时解密（property）
@property
def api_key(self) -> str:
    return decrypt_field(self.api_key_encrypted)

# 写入时加密（setter）
@api_key.setter
def api_key(self, value: str):
    self.api_key_encrypted = encrypt_field(value)
```
**影响范围**：`AIConfigService` 中所有读取 `provider.api_key` 的地方需适配

---

### P0-2：邮件发送静默失败
**文件**：`backend/app/services/email_tracking_service.py:122`
**现状**：调用不存在的 `EmailService.send_raw()`
**修复**：在 `email_service.py` 中新增 `send_raw` 方法：
```python
def send_raw(self, to: str, subject: str, html: str) -> bool:
    """通用邮件发送（开发信/追踪邮件）"""
    if not self.enabled:
        return False
    return self._send_email(to, subject, html)
```
**改动文件**：`backend/app/services/email_service.py`

---

### P0-3：追踪像素无安全防护
**文件**：`backend/app/api/v1/routes/email_tracking.py:12-37`
**现状**：无鉴权、无限速、无 message_id 校验
**修复**：
```python
import re
from collections import defaultdict
from datetime import datetime, timezone

# message_id 格式校验
_MESSAGE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")

# 简易内存限速（每 IP 每分钟 30 次）
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 30
_RATE_WINDOW = 60  # 秒

def _check_rate_limit(ip: str) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_LIMIT:
        return False
    _rate_store[ip].append(now)
    return True

@router.get("/pixel/{message_id}.png")
async def tracking_pixel(message_id: str, request: Request, db: Session = Depends(get_db)):
    # 格式校验
    if not _MESSAGE_ID_RE.match(message_id):
        return Response(content=PIXEL_BYTES, media_type="image/png")
    # 限速
    ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(ip):
        return Response(content=PIXEL_BYTES, media_type="image/png")
    # 记录事件
    record_open_event(db=db, message_id=message_id, ip_address=ip,
                      user_agent=request.headers.get("user-agent", ""))
    db.commit()
    return Response(content=PIXEL_BYTES, media_type="image/png",
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
```

---

### P0-4：Tenant AI Config 未读取 API Key
**文件**：`backend/app/api/v1/routes/tenant_ai_config.py:69-81`
**现状**：`create_config` 未处理 `apiKey` 字段
**修复**：
```python
from app.core.field_crypto import encrypt_field

# 在 create_config 中
api_key = req.get("apiKey", "")
config = TenantAiProviderConfig(
    ...,
    api_key_encrypted=encrypt_field(api_key) if api_key else None,
    ...
)

# 在 get_my_configs 返回时脱敏
"apiKey": "***" if c.api_key_encrypted else None

# update_config 同理
if "apiKey" in req and req["apiKey"]:
    config.api_key_encrypted = encrypt_field(req["apiKey"])
```

---

### P0-5：前端路由未注册
**文件**：`frontend/admin/src/router/index.ts`
**现状**：ProspectingWorkspace 和 OutreachEditor 未注册，404
**修复**：在 ClientLayout children 末尾添加：
```ts
// 工作台路由
{
  path: 'workspace/prospecting',
  name: 'ProspectingWorkspace',
  component: () => import('@/views/workspace/ProspectingWorkspace.vue'),
  meta: { title: '搜客执行台' },
},
{
  path: 'workspace/outreach',
  name: 'OutreachEditor',
  component: () => import('@/views/workspace/OutreachEditor.vue'),
  meta: { title: '写信工作台' },
},
{
  path: 'ai-config',
  name: 'ClientAiConfig',
  component: () => import('@/views/client/ai-config.vue'),
  meta: { title: 'AI 配置' },
},
```

---

### P0-6：OutreachEditor v-html XSS
**文件**：`frontend/admin/src/views/workspace/OutreachEditor.vue:152,230`
**现状**：用户输入和 API 返回内容直接注入 HTML
**修复**：
```ts
// 添加转义函数
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 在 previewHtml computed 中
const previewHtml = computed(() => {
  let html = escapeHtml(form.body)
    .replace(/\n/g, '<br>')
    .replace(/\{\{company_name\}\}/g, escapeHtml(lead.value?.companyName || '[公司名]'))
    .replace(/\{\{evidence_1\}\}/g, escapeHtml(lead.value?.evidenceChain?.[0]?.content || '[证据1]'))
    // ... 所有替换值都 escapeHtml
})
```

---

### P0-7：ScoreRadar ECharts 内存泄漏
**文件**：`frontend/admin/src/components/whatsfinds/ScoreRadar.vue:62,176`
**现状**：无 `onUnmounted`，ECharts 实例和 resize 监听器未清理
**修复**：
```ts
import { ref, onMounted, onUnmounted, watch } from 'vue'

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  // 初始化 ECharts
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
```

---

### P0-8：VariableIcon 未导入
**文件**：`frontend/admin/src/views/workspace/OutreachEditor.vue:88`
**现状**：使用了不存在的 `VariableIcon` 组件
**修复**：替换为已导入的 `NumberOutlined`：
```html
<template #suffix>
  <a-tooltip title="插入变量">
    <NumberOutlined @click="showVariablePicker = !showVariablePicker" style="cursor: pointer" />
  </a-tooltip>
</template>
```

---

## P1 修复方案（10 项核心）

### P1-1：scoreBreakdown 类型不匹配
**文件**：`ProspectingWorkspace.vue:389`
**现状**：传 `{ match, email, evidence, contact }` 对象，ScoreRadar 期望 `ScoreItem[]` 数组
**修复**：
```ts
scoreBreakdown: [
  { label: '匹配度', value: lead.scoreMatch || 0, description: '产品与市场匹配' },
  { label: '邮箱质量', value: lead.scoreEmail || 0, description: '邮箱验证状态' },
  { label: '证据强度', value: lead.scoreEvidence || 0, description: '证据链完整度' },
  { label: '联系人', value: lead.scoreContact || 0, description: '关键人可达性' },
]
```

### P1-2：search_leads 函数不存在
**文件**：`workspace.py:36`
**现状**：调用不存在的函数
**修复**：在 `workspace.py` 中用现有 `ProspectLead` 模型直接查询替代：
```python
# 直接查询已有线索（搜客任务创建后线索入库）
leads = (
    db.query(ProspectLead)
    .filter(ProspectLead.tenant_id == current_user.tenant_id)
    .order_by(ProspectLead.overall_score.desc())
    .limit(50)
    .all()
)
```

### P1-3：generate_outreach_email 函数不存在
**文件**：`workspace.py:149`
**现状**：调用不存在的函数
**修复**：用已有的 AI 调用模式实现：
```python
from app.services.langchain_service import LangChainService

async def generate_outreach_email(lead, tenant_id, db):
    service = LangChainService()
    prompt = f"""根据以下客户信息生成开发信：
公司：{lead.company_name}
国家：{lead.country}
行业：{lead.industry}
请生成主题和正文。"""
    result = await service.generate(prompt)
    return {"subject": result.get("subject", ""), "body": result.get("body", "")}
```

### P1-4~P1-5：租户隔离缺失
**文件**：`workspace.py:142,168`
**修复**：所有查询添加 `ProspectLead.tenant_id == current_user.tenant_id`

### P1-6~P1-8：竞态条件
**文件**：`license_service.py:87,152`
**修复**：使用 `SELECT ... FOR UPDATE`：
```python
lic = (
    db.query(LicenseCode)
    .filter(LicenseCode.code == code)
    .with_for_update()  # 行锁
    .first()
)
```

### P1-9：event_type 无枚举约束
**文件**：`email_tracking_event.py:25`
**修复**：改为 `Enum`

### P1-10：fingerprint_hash 无格式校验
**文件**：`license.py(v2):379`
**修复**：校验长度为 64 字符 + hex 字符集

---

## 执行顺序

```
第一批（独立，可并行）：
  P0-1  API Key 加密         (backend/app/models/ai_config.py)
  P0-2  send_raw 方法        (backend/app/services/email_service.py)
  P0-5  前端路由注册         (frontend/admin/src/router/index.ts)
  P0-7  ScoreRadar 内存泄漏  (ScoreRadar.vue)
  P0-8  VariableIcon 替换    (OutreachEditor.vue)

第二批（依赖第一批）：
  P0-3  追踪像素安全         (依赖 P0-2)
  P0-4  tenant config Key    (依赖 P0-1)
  P0-6  XSS 修复             (OutreachEditor.vue)
  P1-1  scoreBreakdown 类型  (依赖 P0-5 路由)

第三批（后端串联修复）：
  P1-2  search_leads 替代    (workspace.py)
  P1-3  outreach 生成替代    (workspace.py)
  P1-4  租户隔离             (workspace.py)
  P1-6  竞态条件             (license_service.py)
```

---

## 验证清单

- [ ] `python -m py_compile` 所有修改的后端文件
- [ ] `npx vue-tsc --noEmit` 无新增错误
- [ ] 前端访问 `/client/workspace/prospecting` 不再 404
- [ ] 前端访问 `/client/workspace/outreach` 不再 404
- [ ] 追踪像素 `/api/v1/tracking/pixel/test.png` 返回 1x1 PNG
- [ ] AI Key 配置页可正常创建/读取/更新
- [ ] ScoreRadar 组件卸载后无内存泄漏
# P1 全量规划：5 项任务实施计划

> 基于 WhatsFinds AI + GoodJob CRM 吸收优化
> 规划日期：2026-07-20 | 目标周期：2 周

---

## 现状基线（探索结论）

### 已有基础设施
| 组件 | 现状 | 复用价值 |
|------|------|----------|
| `ProspectLead` 模型 | 有 `fit_score`/`engagement_score`/`overall_score`/`email_verified`/`status` | **高** — 直接扩 4 维子分字段 |
| `unified_geo_score_service` | 有产品覆盖度评分 + AI搜索探针 | **中** — 拆为 `match_score` / `evidence_score` |
| `email_service` | 有 SMTP 发信（询盘通知） | **高** — 扩展为多通道 + 追踪 |
| `CustomerFinder.vue` | 有搜索弹窗 + 筛选 + 列表 + 详情抽屉 | **高** — 在详情抽屉中嵌入证据链/雷达图 |
| `SearchSyntaxPreview` | P0 已完成 | **高** — 搜客执行台直接集成 |
| `EvidenceChain` / `ScoreRadar` | P0 已完成 | **高** — 在详情页直接集成 |

### 缺失项
| 缺失 | 影响 P1 任务 |
|------|-------------|
| `evidence_chain` 字段 (ProspectLead) | P1-1, P1-4 |
| `score_breakdown` 字段 (ProspectLead) | P1-4 |
| 邮件追踪像素/打开事件模型 | P1-3 |
| 邮件发送队列/批量机制 | P1-3 |
| 写信变量解析器 | P1-2 |
| 邮件版本管理 | P1-2 |
| 设备指纹模型 | P1-5 |
| 授权码模型 | P1-5 |

---

## 任务依赖关系

```
P1-4 (评分维度拆解)
  └─→ 依赖 ProspectLead 模型扩展
  └─→ P1-1 (搜客执行台) 需要用到新评分展示
  └─→ P1-2 (写信台) 需要用到评分判断优先级

P1-3 (邮件追踪像素)
  └─→ 依赖 EmailTrackingEvent 模型
  └─→ P1-2 (写信台) 需要追踪能力

P1-5 (设备指纹/授权码)
  └─→ 独立，可并行
```

**推荐执行顺序**：`P1-4 → P1-1 → P1-2 → P1-3 → P1-5`（P1-5 可并行）

---

## P1-1：搜客执行台单页聚合

### 设计
一个单页完成「搜客 → 画像 → 写信 → 追踪」四步线性流。

**页面结构**：
```
/workspace/prospecting
├── Step 1: 搜客条件输入 (SearchSyntaxPreview 集成)
├── Step 2: 候选结果列表 + EvidenceChain + ScoreRadar
├── Step 3: 快速写信入口 (跳转 P1-2 OutreachEditor)
└── Step 4: 追踪状态 (已发/已开/已回复)
```

### 文件清单
| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | `frontend/admin/src/views/workspace/ProspectingWorkspace.vue` | 主页面 |
| **新建** | `frontend/admin/src/components/workspace/ProspectStepBar.vue` | 步骤条 |
| **新建** | `frontend/admin/src/components/workspace/ProspectResultCard.vue` | 结果卡片 |
| **修改** | `frontend/admin/src/views/sales/CustomerFinder.vue` | 添加跳转入口 |
| **新建** | `backend/app/api/v1/routes/workspace_prospecting.py` | 聚合路由 |
| **修改** | `backend/app/models/prospect_lead.py` | 扩展 `evidence_chain` JSON 字段 |

### 后端路由设计
```python
# GET  /workspace/prospecting/tasks          - 搜客任务列表
# POST /workspace/prospecting/search         - 创建搜客任务
# GET  /workspace/prospecting/leads          - 候选线索列表（分页+筛选）
# GET  /workspace/prospecting/leads/{id}     - 线索详情（含 evidence_chain）
# POST /workspace/prospecting/leads/{id}/convert  - 转为客户/商机
```

### 前端页面设计
- **Step 1 区域**：`SearchSyntaxPreview` + 产品词/市场/类型/排除词表单
- **Step 2 区域**：卡片列表（公司名/评分/来源/证据数），点击展开 `EvidenceChain` + `ScoreRadar`
- **Step 3 区域**：「发开发信」按钮跳转 OutreachEditor，带 `lead_id` 参数
- **Step 4 区域**：表格展示已发线索的打开/回复状态（来自 P1-3 追踪数据）

### 预估工时：5 天

---

## P1-2：AI 写信工作台 (OutreachEditor)

### 设计
左侧画像摘要 + 右侧编辑器（变量插入/预览/A/B 版本），集成 P0 已完成的组件。

**页面结构**：
```
/workspace/outreach?lead_id=xxx
├── 左侧: 画像摘要 (EvidenceChain + ScoreRadar)
├── 右侧上: 邮件编辑器 (Tiptap + 变量插入器)
├── 右侧下: 预览区 (HTML 渲染 + 移动端/桌面端切换)
└── 底部: 发送/存草稿/切换 A/B 版本
```

### 文件清单
| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | `frontend/admin/src/views/workspace/OutreachEditor.vue` | 主页面 |
| **新建** | `frontend/admin/src/components/workspace/EmailVariablePicker.vue` | 变量插入器 |
| **新建** | `frontend/admin/src/components/workspace/EmailPreview.vue` | HTML 预览 |
| **新建** | `frontend/admin/src/components/workspace/EmailVersionTabs.vue` | A/B 版本 |
| **新建** | `backend/app/api/v1/routes/workspace_outreach.py` | 写信台路由 |
| **新建** | `backend/app/models/email_draft.py` | 草稿/A/B 版本模型 |
| **新建** | `backend/app/services/variable_resolver.py` | 变量解析器 |

### 变量系统设计
```python
# 支持的变量
VARIABLES = {
    "{{company_name}}": "ProspectLead.company_name",
    "{{contact_name}}": "ProspectLead.first_name + last_name",
    "{{country}}": "ProspectLead.country",
    "{{industry}}": "ProspectLead.industry",
    "{{evidence_1}}": "ProspectLead.evidence_chain[0].content",
    "{{evidence_2}}": "ProspectLead.evidence_chain[1].content",
    "{{product_advantage}}": "Tenant.product_advantages",
    "{{sender_name}}": "User.name",
    "{{sender_company}}": "Tenant.company_name",
    "{{tracking_pixel}}": "自动生成的追踪像素 HTML",
    "{{unsubscribe_link}}": "自动生成的退订链接",
}
```

### 后端路由设计
```python
# POST /workspace/outreach/drafts              - 保存草稿
# GET  /workspace/outreach/drafts?lead_id=xxx  - 获取草稿
# POST /workspace/outreach/ai-generate         - AI 生成邮件（调用 TenantAiProviderConfig）
# POST /workspace/outreach/send                - 发送邮件
# GET  /workspace/outreach/versions?lead_id=   - 获取 A/B 版本列表
```

### 预估工时：5 天

---

## P1-3：邮件追踪像素服务

### 设计
在邮件 HTML 中注入 1x1 透明像素图片，每次打开触发回调，记录打开时间/IP/User-Agent。

**架构**：
```
用户打开邮件
  → 加载 <img src="https://domain/tracking/pixel/{message_id}.png">
  → GET /tracking/pixel/{message_id}.png
  → 记录 EmailOpenEvent（message_id, ip, user_agent, opened_at）
  → 返回 1x1 透明 PNG（带 Cache-Control: no-cache）
```

### 文件清单
| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | `backend/app/models/email_tracking_event.py` | 打开/点击事件模型 |
| **新建** | `backend/app/services/email_tracking_service.py` | 追踪服务 |
| **新建** | `backend/app/api/v1/routes/email_tracking.py` | 像素路由（无需登录） |
| **新建** | `backend/app/services/bulk_email_sender.py` | 批量发信队列 |
| **修改** | `backend/app/models/prospect_lead.py` | 扩展 `last_opened_at` / `open_count` 字段 |
| **修改** | `frontend/admin/src/views/sales/CustomerFinder.vue` | 详情抽屉展示追踪数据 |

### 像素路由（无需鉴权）
```python
@router.get("/tracking/pixel/{message_id}.png")
async def tracking_pixel(message_id: str, request: Request, db: Session):
    """1x1 追踪像素，每次打开记录事件"""
    event = EmailOpenEvent(
        message_id=message_id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(event)
    # 更新 ProspectLead 的 last_opened_at / open_count
    db.commit()
    # 返回 1x1 透明 PNG
    return Response(content=PIXEL_BYTES, media_type="image/png",
                    headers={"Cache-Control": "no-cache, no-store"})
```

### 批量发信方案（兜底群发）
```python
class BulkEmailSender:
    """多通道批量发信，支持 SMTP / SendGrid / Mailgun 自动兜底"""

    def __init__(self):
        self.channels = [
            SmtpChannel(),       # 自建 SMTP（首选）
            SendGridChannel(),   # SendGrid（第二选择）
            MailgunChannel(),    # Mailgun（兜底）
        ]

    async def send_batch(self, drafts: list[EmailDraft]):
        """逐封发送，失败自动切换下一个通道"""
        for draft in drafts:
            for channel in self.channels:
                if channel.available:
                    try:
                        await channel.send(draft)
                        draft.status = "sent"
                        break
                    except Exception:
                        draft.status = "retry"
                        continue
            db.commit()
```

### 预估工时：5 天

---

## P1-4：画像评分维度拆解

### 设计
将现有的单分数 `overall_score` 拆解为 4 维子分，复用 `ScoreRadar` 展示。

**评分维度**（推荐方案 — 基于现有模型扩展）：
| 维度 | 字段 | 计算逻辑 | 权重 |
|------|------|----------|------|
| **匹配度** | `score_match` | 产品词覆盖 + 行业匹配 + 国家匹配 | 30% |
| **邮箱可信度** | `score_email` | email_verified(valid=90, risky=50, unknown=30, invalid=0) | 25% |
| **证据完整度** | `score_evidence` | len(evidence_chain) / 5 * 100 (满分需 5 条) | 25% |
| **联系人完整度** | `score_contact` | 有邮箱+电话+职位+LinkedIn 各 25 分 | 20% |

**综合分公式**：
```python
overall_score = int(
    score_match * 0.30 +
    score_email * 0.25 +
    score_evidence * 0.25 +
    score_contact * 0.20
)
```

### 文件清单
| 操作 | 文件 | 说明 |
|------|------|------|
| **修改** | `backend/app/models/prospect_lead.py` | 新增 4 维子分字段 |
| **新建** | `backend/app/services/prospect_scorer.py` | 评分计算服务 |
| **修改** | `backend/app/services/lead_generation_service.py` | 搜客时自动计算评分 |
| **修改** | `frontend/admin/src/views/sales/CustomerFinder.vue` | 详情抽屉嵌入 ScoreRadar |

### 模型迁移
```sql
ALTER TABLE prospect_leads
  ADD COLUMN score_match INTEGER DEFAULT 0,
  ADD COLUMN score_email INTEGER DEFAULT 0,
  ADD COLUMN score_evidence INTEGER DEFAULT 0,
  ADD COLUMN score_contact INTEGER DEFAULT 0,
  ADD COLUMN evidence_chain JSONB DEFAULT '[]',
  ADD COLUMN last_opened_at TIMESTAMPTZ,
  ADD COLUMN open_count INTEGER DEFAULT 0;
```

### 预估工时：3 天

---

## P1-5：设备指纹 + 授权码体系

### 设计
参照 WhatsFinds 的设备绑定 + 授权码激活流程。

**流程**：
```
用户首次登录 → 前端生成设备指纹 → 后端绑定设备ID
购买套餐 → 后端生成授权码 (TL1.xxxxx.xxxxx)
输入授权码 → 绑定设备 → 激活 → 到期续费
```

### 文件清单
| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | `backend/app/models/license.py` | 授权码 + 设备绑定 + 套餐订单 |
| **新建** | `backend/app/services/license_service.py` | 激活/续费/设备绑定服务 |
| **新建** | `backend/app/api/v1/routes/license.py` | 授权路由 |
| **新建** | `frontend/admin/src/views/system/License.vue` | 授权管理页 |
| **新建** | `frontend/admin/src/components/whatsfinds/DeviceFingerprintBanner.vue` | 未授权顶栏 |

### 模型设计
```python
class DeviceFingerprint(Base):
    """设备指纹"""
    __tablename__ = "device_fingerprints"
    id = Column(UUID_TYPE, primary_key=True)
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), index=True)
    fingerprint_hash = Column(String(64), unique=True, index=True)  # SHA256
    device_info = Column(JSON)  # {browser, os, screen, timezone, ...}
    first_seen_at = Column(DateTime(timezone=True))
    last_seen_at = Column(DateTime(timezone=True))

class LicenseCode(Base):
    """授权码"""
    __tablename__ = "license_codes"
    id = Column(UUID_TYPE, primary_key=True)
    code = Column(String(50), unique=True, index=True)  # TL1.xxxxx.xxxxx
    plan_type = Column(String(20))  # half_year / yearly
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    device_fingerprint_id = Column(UUID_TYPE, ForeignKey("device_fingerprints.id"), nullable=True)
    activated_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="pending")  # pending / activated / expired / revoked

class LicenseOrder(Base):
    """授权订单"""
    __tablename__ = "license_orders"
    id = Column(UUID_TYPE, primary_key=True)
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), index=True)
    license_code_id = Column(UUID_TYPE, ForeignKey("license_codes.id"))
    plan_type = Column(String(20))
    amount = Column(Integer)  # 分
    payment_method = Column(String(30))  # alipay / wechat / bank / other
    payment_ref = Column(String(200))
    status = Column(String(20), default="pending")  # pending / confirmed / expired
    confirmed_by = Column(UUID_TYPE, nullable=True)
    confirmed_at = Column(DateTime(timezone=True))
```

### 预估工时：5 天（可并行）

---

## 执行排期

```
Week 1 (7/21 - 7/25)
  Mon-Tue: P1-4 评分维度拆解 (3天) ─────────┐
  Wed-Thu: P1-1 搜客执行台 (5天) ────────────┤ 串行：P1-4 完成后开始 P1-1
  Fri:     P1-1 继续                         │
  (并行)   P1-5 设备指纹/授权码 (5天) ────────┘ 独立并行

Week 2 (7/28 - 8/1)
  Mon-Tue: P1-2 AI写信工作台 (5天) ──────────┐
  Wed-Thu: P1-2 继续                         │
  Fri:     P1-3 邮件追踪像素 (5天) ──────────┘  P1-3 可提前1天开始
```

---

## 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 邮件送达率低 | 高 | P1-3 效果打折 | 多通道兜底 + 退信检测 + 退订机制 |
| 像素被邮箱客户端屏蔽 | 中 | 打开追踪不准 | 补充 Link-based 追踪 + IMAP 轮询 |
| 评分算法不准 | 中 | 用户不信任 | 先用简单规则，后续用实际数据调参 |
| 设备指纹被重置 | 低 | 用户换设备后失效 | 备用邮箱验证 + 管理员手动解绑 |

---

## 完成标准

- [ ] P1-1：搜客执行台单页可完成「搜 → 选 → 发」全流程
- [ ] P1-2：写信台支持变量插入、预览、A/B 版本、发送
- [ ] P1-3：邮件发送后可追踪打开率，前端展示追踪数据
- [ ] P1-4：客户详情页显示 4 维雷达图，评分逻辑可解释
- [ ] P1-5：设备绑定 + 授权码激活流程完整，订单状态机正确
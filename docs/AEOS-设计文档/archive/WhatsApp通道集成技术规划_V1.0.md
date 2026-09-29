# WhatsApp 通道集成技术规划与代码级指导 V1.0

> 基准：《三方文档对峙与合并结论》冻结架构（Control Plane = 优丁 FastAPI 单体；Execution Plane 平级 Adapter；Revenue OS = meter_events+pricing_rules；Experience Engine；租户隔离优先；Skill 版本化；Evidence 证据机制）。
> 参考源：GoodJob CRM `whatsapp-plugin/`（实测扫描结论见《开源项目嫁接融合可行性报告》）。
> 定位裁决：**GoodJob 的通道能力（收发/会话/模板/媒体/凭证）确实更强，但其编排是"固定节奏自动化"；优丁的 Hermes/UBrain/Evolution 智能编排更强。因此本方案 = 吸收其通道设计思想，通道本体按 Meta 官方 Cloud API 用 Python 重写为 Channel Adapter，编排权 100% 留在 Control Plane。**
> ⚠️ 红线：GoodJob 的 Baileys（非官方 WhatsApp Web 协议）通道**永不引入**（封号 + ToS + 其 GPL-3.0 许可证）。只借鉴架构思路，不复制任何该插件代码。

---

# 一、能力差距分析

## 1.1 双方能力对照（实测）

| 能力域 | GoodJob whatsapp-plugin | 优丁现状 | 差距 |
|---|---|---|---|
| 通道接入 | Baileys + Meta 官方双通道，`free_first/official_first/hybrid` 三策略 | `whatsapp_business_service.py`（官方 API 雏形） | 优丁只做官方通道是对的；差距在**完成度**而非方向 |
| 消息模型 | 账号级联系人/会话/消息三表 + 幂等隔离 + 状态回执（sent/delivered/read） | 散落在 `im_chat.py`/`im_routing_and_specs.py`，无 WhatsApp 专属回执链 | **大差距**：需专属消息/会话表 + 回执状态机 |
| 会话状态机 | 24 小时客服窗口管理、会话开关与分类（营销/实用/认证） | 无窗口概念 | **大差距**：窗口状态机是计费与合规的前提 |
| 模板消息 | Meta 审核模板 + 变量填充 + 窗口外发送 | 无 | **大差距** |
| 凭证管理 | AES-256-GCM AuthState + SESSION_MASTER_KEY + 密钥与库成对备份 | 密钥散落（已在整改，087 迁移） | **中差距**：并入 Credential Vault 即可 |
| Webhook | Graph 归属校验 + 签名校验 + 入站文本 + 状态回执 | `im_channel_webhook_service.py`（通用） | **中差距**：需 WhatsApp 专属签名与事件解析 |
| 媒体处理 | 附件保留策略 + 收发 | `media_*` 服务族很强但无 WhatsApp 媒体上下行 | **中差距**：对接现有 media 服务即可 |
| 上线检查中心 | 商业上线检查清单（身份/Token/HTTPS/Webhook/自动化逐项验证） | 无对应物 | **借鉴**：做成 `production_readiness_service` 的检查项扩展 |
| AI 自动化 | 增量消息周期分析→每日待办；保留模型/提示词版本/证据/人工反馈；模型故障降级规则引擎 | 优丁有更强的 Hermes/UBrain/Evolution 编排 | **优丁反超**：GoodJob 是固定节奏，优丁是意图驱动+经验飞轮 |
| 实时推送 | Socket.IO | 有 `push_notification_service`/WebSocket | 持平 |
| 多租户 | 单租户单实例（明示边界） | 原生多租户 | **优丁反超** |

## 1.2 值得借鉴的设计（思想级）

1. **账号级隔离模型**：一切联系人/会话/消息挂在"通道账号"之下，天然支持一租户多号码 → 对应我方 `channel_accounts` 概念。
2. **三策略接入抽象**（`free_first/official_first/hybrid`）：策略只影响"新账号推荐"，不迁移/合并已有账号——借鉴为"通道能力开关"的策略模式（官方通道内也可做"自动回复优先/人工优先/混合"三策略）。
3. **幂等隔离**：消息以 `external_message_id` 唯一，重复投递不重入 → 借鉴为 Webhook 幂等。
4. **AI 动作留证**：模型/提示词版本 + 证据消息 + 人工确认/忽略反馈 + 规则降级 → 与我方 Evidence + Skill 版本化完全同构，直接套用现有机制。
5. **上线检查中心**：逐项验证外部依赖就绪 → 并入 `production_readiness_service`。

## 1.3 不能直接复用的部分（技术栈/许可证）

| 项 | 原因 |
|---|---|
| 插件全部代码（TS/Express/Socket.IO/PGlite） | Node 栈，与 Python/FastAPI 不兼容；且属 GPL-3.0 工作区 |
| Baileys 通道 | 非官方协议：封号风险 + ToS 违反 + GPL 依赖链（libsignal） |
| 其单租户部署假设 | 优丁是多租户 SaaS，所有移植设计必须加 `tenant_id` + Vault 绑定 |
| 其 MySQL/PGlite 双轨存储 | 优丁统一 PostgreSQL + Alembic |

---

# 二、完整技术规划

## 2.1 架构定位（冻结口径落位）

```
Control Plane（优丁后端，唯一真相源）
├── channel_accounts（现有概念，平台账号主表）
│     └── whatsapp_accounts（WABA/号码/凭证 ref→Vault）
├── whatsapp_conversations / whatsapp_messages（会话与消息真相源）
├── whatsapp_templates（模板，含版本与审核状态）
├── Policy Engine（发送前裁决：窗口/配额/合规/人审）
└── Hermes/UBrain（智能编排：意图识别→回复生成→跟进策略）

Execution Plane
└── WhatsAppChannelAdapter（新增，与 DeerFlow/n8n 同级）
      ├── MetaGraphClient（Cloud API 封装）
      ├── WebhookReceiver（签名校验/幂等/解析）
      ├── MediaBridge（对接现有 media_* 服务）
      └── TemplateManager（模板同步/变量填充/审核轮询）

Revenue OS
└── meter_events（meter='whatsapp_conversation'，按会话分类+国家计费）

Experience Engine
└── task_traces/evidence（每次 AI 回复留证：skill_version/prompt_ref/人工反馈）
```

调度规则：**入站消息 → Control Plane 路由（租户识别→意图评分→编排决策）→ 出站必须经 Policy 裁决**。WhatsApp 只是通道，不做任何业务决策——这是与 GoodJob"插件自带自动化节奏"的本质区别。

## 2.2 模块划分

| 模块 | 职责 | 落位 |
|---|---|---|
| `whatsapp_gateway_service` | 收发统一入口、幂等、限流、计费埋点 | `app/services/whatsapp/` |
| `meta_graph_client` | Cloud API HTTP 封装（发送/媒体/模板/洞察） | 同上 |
| `webhook_receiver` | 签名验证、验证挑战、事件解析、幂等入队 | 同上 |
| `conversation_state_machine` | 24h 窗口 + 会话分类 + 开/关/升级状态机 | 同上 |
| `template_manager` | 模板 CRUD、提审、状态轮询、版本化 | 同上 |
| `media_bridge` | 媒体上传/下载/病毒扫描钩子/保留策略 | 对接现有 `media_*` |
| `whatsapp_adapter` | Execution Plane 契约实现（Adapter Protocol） | `app/services/adapters/` |
| 计费埋点 | 会话开启事件 → `meter_events` | Celery beat 汇总 |

## 2.3 数据模型（新增/扩展，走 Alembic 新迁移）

```
channel_accounts（现有，扩展）
  + channel_type='whatsapp' 判别
  + tenant_id（已有）

whatsapp_accounts（新）
  id UUID PK, tenant_id FK→tenants, channel_account_id FK→channel_accounts
  waba_id VARCHAR, phone_number_id VARCHAR, display_phone VARCHAR
  token_vault_ref VARCHAR        -- 凭证在 Vault（087 迁移），此处仅引用
  messaging_limit_tier VARCHAR   -- 250/1K/10K/100K/UNLIMITED
  quality_status VARCHAR         -- green/yellow/red（Meta 质量评级）
  status VARCHAR                 -- pending_verification/active/suspended
  webhook_verify_token_ref VARCHAR
  created_at/updated_at

whatsapp_templates（新，版本化）
  id, tenant_id, account_id, meta_template_id, name, language,
  category ENUM('marketing','utility','authentication'),
  status ENUM('draft','submitted','approved','rejected','paused'),
  components JSONB,              -- header/body/footer/buttons
  version INT, parent_template_id,      -- Skill 版本化原则的通道侧投影
  submitted_at/approved_at, rejection_reason

whatsapp_conversations（新）
  id, tenant_id, account_id, contact_wa_id, contact_phone,
  category ENUM('marketing','utility','authentication','service'),
  status ENUM('open','expired','closed'),
  opened_at, expires_at,         -- 24h 窗口
  meta_conversation_id, last_message_at,
  intent_score INT, assigned_agent_id,   -- 编排入口
  UNIQUE(account_id, meta_conversation_id)

whatsapp_messages（新）
  id, tenant_id, conversation_id, direction ENUM('inbound','outbound'),
  meta_message_id UNIQUE,        -- 幂等键
  msg_type ENUM('text','template','image','video','document','audio','interactive'),
  content JSONB, media_artifact_id FK→现有媒体体系,
  status ENUM('accepted','sent','delivered','read','failed'),
  failure_code, failure_reason,
  generated_by JSONB,            -- {skill_id, skill_version, model, prompt_ref}（Evidence）
  human_approved_by, created_at

whatsapp_webhook_events（新，幂等+审计）
  id, tenant_id NULL, account_id NULL, meta_event_id UNIQUE,
  payload_ref VARCHAR,           -- 原始报文存对象存储
  processed BOOL, error, created_at
```

与现有表关系：`tenants 1─N channel_accounts 1─1 whatsapp_accounts 1─N conversations 1─N messages`；模板独立挂账号；计费经 `meter_events.ref_id → conversations.id`。

## 2.4 API 设计（关键接口）

```
# 出站发送（内部服务间也走此契约）
POST /api/v1/whatsapp/messages
  Request: {tenant_id*, account_id*, to_wa_id*, type*, content{...}|template{name,language,components}, idempotency_key*}
  Response 202: {message_id, status:'accepted', estimated_window:'open'}
  422/403: Policy 拒绝（窗口关闭且无可用模板 / 配额超限 / 合规拦截）

# Meta Webhook（公开路径，签名校验）
GET  /api/v1/whatsapp/webhook/{account_id}?hub.mode&hub.verify_token&hub.challenge → 200 challenge
POST /api/v1/whatsapp/webhook/{account_id} → 200（先落库再异步处理，3 秒内必须返回）

# 模板管理
POST   /api/v1/whatsapp/templates            （创建+提审）
GET    /api/v1/whatsapp/templates?status=
POST   /api/v1/whatsapp/templates/{id}/submit
GET    /api/v1/whatsapp/templates/{id}/status （轮询 Meta 审核）

# 会话与账号
GET  /api/v1/whatsapp/conversations?status=&intent_gte=
POST /api/v1/whatsapp/accounts/{id}/verify （上线检查单项）
GET  /api/v1/whatsapp/accounts/{id}/readiness （上线检查中心）
```

所有租户侧接口走现有 JWT/RBAC 中间件；Webhook 路径豁免认证但强制签名校验 + 限流。

## 2.5 Meta Cloud API 对接

1. **开通**：Embedded Signup（租户在 Meta 侧完成）→ 我方拿 `waba_id` + `phone_number_id`；或平台自持 Meta App 走系统用户。
2. **Token**：优先**系统用户长期 Token**（不过期，推荐）；若用短期 Token 需 24h 内换长期。Token 一律入 Credential Vault（AAD 绑定 `tenant_id+account_id`），运行时短期解密，绝不进日志/响应。
3. **Webhook 订阅**：`messages`、`message_template_status_update`、`account_alerts` 三类；`X-Hub-Signature-256 = HMAC-SHA256(raw_body, app_secret)` 逐字节校验。
4. **限流策略**（三层）：
   - Meta 层：尊重 `x-business-use-case-usage` 头，触碰限自动退避入队；
   - 租户层：`plan_gate_service` 配额（日发送上限/并发会话上限）；
   - 号码层：消息分级上限（250/1K/10K…）跟踪，超限自动降级为模板队列等待。
5. **24 小时窗口**：入站开/续窗；窗口内自由回复；窗口外只允许发审核通过的模板（状态分类准确计费）。

## 2.6 计费集成（Revenue OS）

Meta 按 **24h 会话×分类×国家**计费（非按条），我方计量对齐：

```
触发点：会话开启（open）与分类升级（service→marketing）
→ INSERT meter_events(meter='whatsapp_conversation', quantity=1,
     ref_id=conversation.id, dims={category, country, account_id})
→ Celery beat 汇总：查 pricing_rules（按 category×country 分层）
→ 成本侧：按 Meta 账单成本入账；收入侧：按租户套餐（含免费额度）
```

另埋点：`whatsapp_template_submission`（模板提审服务费，可选）、`whatsapp_media_gb`（媒体存储，并入现有存储计量）。

---

# 三、详细代码级技术指导

> 以下为签名与伪代码指导，**本次不落地**。目录：`app/services/whatsapp/`。

## 3.1 核心类签名

```python
# meta_graph_client.py
class MetaGraphClient:
    def __init__(self, vault: CredentialVault, http: httpx.AsyncClient): ...
    async def send_message(self, account: WhatsappAccount, payload: dict) -> MetaSendResult: ...
    async def send_template(self, account, template: WhatsappTemplate, to: str, vars_: list) -> MetaSendResult: ...
    async def upload_media(self, account, artifact_id: str) -> str: ...     # 返回 media_id
    async def download_media(self, account, media_id: str) -> bytes: ...
    async def create_template(self, account, spec: TemplateSpec) -> str: ...
    async def get_template_status(self, account, meta_template_id: str) -> str: ...
# 异常：MetaRateLimitError(重试头) / MetaAuthError(触发重授权流程) / MetaApiError(带 error.code)

# webhook_receiver.py
class WebhookReceiver:
    def verify_signature(self, raw: bytes, signature_header: str, app_secret: str) -> bool
    async def handle_challenge(self, params: dict, account) -> str | None
    async def ingest(self, account, raw: bytes) -> None:
        # 1. 幂等：meta_event_id 冲突即返回
        # 2. 落 whatsapp_webhook_events（payload 转存对象存储）
        # 3. 发布内部事件 → Celery 队列（3 秒红线内必须完成入队）

# conversation_state_machine.py
class ConversationStateMachine:
    TRANSITIONS = {
        'new_inbound':   {None: 'open'},                 # 开窗
        'inbound':       {'open': 'open'},               # 续窗 24h
        'expiry':        {'open': 'expired'},
        'template_sent': {'expired': 'open'},            # 营销/实用模板重新开窗（按 Meta 规则）
        'close':         {'open': 'closed'},
    }
    def apply(self, conv, event) -> Conversation: ...    # 行锁 + 事务内转移

# whatsapp_gateway_service.py
class WhatsAppGateway:
    async def send(self, ctx: TenantContext, cmd: SendCommand) -> SendResult:
        # 1. Policy 裁决（窗口/配额/合规/需人审?）
        # 2. 幂等（idempotency_key）
        # 3. 出站（文本或模板降级）
        # 4. 回执追踪登记 + 计费触发判定
        # 5. Evidence 记录（skill_version/model/prompt_ref）
```

## 3.2 异常处理策略（统一矩阵）

| 异常 | 策略 |
|---|---|
| Meta 429/限流 | 指数退避 ≤3 次 → 转 `RETRY` 队列（Celery countdown）→ 超限转人工队列 |
| Token 失效（code 190） | 标记账号 `suspended` → 通知租户重授权 → 期间出站全拒 |
| 模板被拒 | 状态 `rejected` + 原因回写 → 触发 Hermes 生成替代文案任务（走人审） |
| 窗口外无模板 | Policy 返回 403 + 建议动作（推荐可用模板列表） |
| 媒体下载失败 | 消息落库 `media_pending`，异步重试，不阻塞会话 |
| 签名校验失败 | 401 + 安全事件日志（`security_event_service`）+ 限流计数 |

禁止：静默吞异常、无限重试、把 Meta 错误原文透传给前端（脱敏，参考 GoodJob `sanitizedAiErrorText` 的思路）。

## 3.3 路由与 Pydantic（示例）

```python
# api/v1/routes/whatsapp.py
router = APIRouter()

class SendRequest(BaseModel):
    account_id: UUID; to_wa_id: str = Field(pattern=r"^\d{7,19}$")
    type: Literal['text','template']; content: dict | None = None
    template: TemplateRef | None = None
    idempotency_key: str = Field(min_length=8, max_length=64)

@router.post("/messages", status_code=202)
async def send_message(req: SendRequest, ctx=Depends(tenant_ctx), db=Depends(get_db)):
    result = await WhatsAppGateway(db).send(ctx, SendCommand(**req.dict()))
    return success_response(data=result)

@router.api_route("/webhook/{account_id}", methods=["GET","POST"])
async def webhook(account_id: UUID, request: Request, db=Depends(get_db)):
    # GET=验证挑战；POST=签名校验→幂等落库→200；全程不抛 5xx 给 Meta（防退订）
```

注册方式：并入现有 `routes/__init__.py` 的自动发现（注意把 `whatsapp` 加入 `custom_prefix_modules` 排除集，防止重复注册——吸取幽灵路由教训）。

## 3.4 n8n 集成点（仅外部联动，不进决策）

| 事件 | n8n workflow |
|---|---|
| `whatsapp.conversation.opened`（intent_score≥60） | 销售提醒（邮件/企微）+ CRM 任务创建 |
| `whatsapp.message.failed`（连续 3 次） | 运维告警 + 通道健康巡检 |
| `whatsapp.conversation.expired`（未成交） | 转 Nurture 序列（对接现有 `nurture_execution_scheduler`） |
| `whatsapp.template.approved/rejected` | 通知租户 + 营销日历更新 |

方向铁律：n8n 只消费事件做通知/外部系统联动；**任何"该不该回复、回复什么"的决策回优丁**。

## 3.5 Hermes/UBrain/DeerFlow 交互（编排是优丁的强项，放大它）

```
入站消息 → webhook → conversation 更新
  → UBrain 意图识别（复用 inquiry_scoring_service 权重体系）
  → 路由决策（Hermes）：
      A. 高意图（≥80）：转人工 + 生成回复草稿（人审发送，走 approval_gate）
      B. 中意图：UBrain 智能回复（smart_reply skill，版本化）→ Policy 裁决 → 自动发送
      C. 复杂技术询价：触发 DeerFlow 深度任务（产品匹配/计算器）→ 结果经模板发送
  → 出站记录 generated_by{skill_id, skill_version, model, prompt_ref}（Evidence）
  → 人工纠正/客户反馈 → ExperienceEntry（成功/失败经验入飞轮）
```

Skill 版本化落地：`smart_reply`、`template_copywriting` 等回复类技能一律注册进 `skills` 表（迁移 083），灰度走 `evolution/canary`。

## 3.6 安全要点

1. **Webhook 签名**：HMAC-SHA256 逐字节校验，失败即 401；`app_secret` 入 Vault。
2. **防 Prompt Injection**：入站消息内容一律视为**不可信输入**——进入 LLM 前做隔离包装（结构化标记 + 禁止执行指令白名单）；Agent 的工具权限不因消息内容扩大（沿用 GoodJob"Skill 不得扩权"原则与我方 Policy 禁用集）。
3. **租户级频率限制**：发送侧三层（租户配额/号码分级/会话窗口）；接收侧按 `account_id` 限流（`rate_limit.py` 扩展）。
4. **敏感数据**：消息正文默认不加密但受 RLS 保护；媒体走签名 URL；导出走 `data_export_guard`；GDPR 删除走现有 `gdpr` 服务。
5. **密钥治理**：Token 轮换、Vault AAD 绑定、日志脱敏（手机号中段打码）。

## 3.7 测试策略

| 层 | 覆盖点 |
|---|---|
| 单元 | 状态机全转移矩阵（含非法转移拒绝）；签名校验正反例；幂等去重；限流三层判定；计费触发条件（开窗/升级） |
| 集成 | Webhook 重放测试（录制的 Meta 报文）；发送→回执链（mock Meta）；双租户隔离（A 租户报文路由不到 B）；Policy 拒绝路径 |
| Sandbox 联调 | ① Meta 开发者平台建 App + 测试号码 → ② 配置 Webhook 指向内网穿透（ngrok，仅开发）→ ③ 验证挑战 → ④ 沙箱号互发文本/模板/媒体 → ⑤ 回执验证 → ⑥ 模板提审（沙箱自动通过）→ ⑦ 限流模拟 |
| E2E | Playwright：admin 绑定账号→发送→查看回执→模板管理全流程 |

---

# 四、实施路线图

## MVP（2-3 周）：官方通道收发闭环
- 交付：数据模型迁移（1 个）、`meta_graph_client`、Webhook 接收、会话状态机、文本收发、模板只读同步、`meter_events` 开窗埋点
- 验收：Meta Sandbox 双向收发成功；回执状态完整流转；重复投递幂等；双租户隔离测试 0 泄漏；每会话产生计量事件

## V1（3-4 周）：智能编排接入
- 交付：模板管理+提审+版本化、媒体上下行（对接 media_*）、UBrain 意图路由三策略、智能回复 Skill 注册进 `skills` 表、Evidence 留证、n8n 四类事件、上线检查中心
- 验收：中意图消息自动回复成功率 ≥90%（评测集）；高意图 100% 转人审；AI 回复全部带 `skill_version`；ExperienceEntry 可回收人工纠正

## V2（4-6 周）：规模化与商业化
- 交付：多账号/多号码管理、广播营销（模板批量，严格合规窗口）、号码质量监控与限流分层、定价规则（category×country）、WhatsApp 通道收入看板、DeerFlow 深度任务触发
- 验收：单租户 ≥3 号码并行；计费与 Meta 账单对账误差 0；质量降级（yellow/red）自动告警

## 风险清单

| 风险 | 规避 |
|---|---|
| Meta App/模板审核周期不可控 | MVP 用沙箱全功能验证；生产审核提前 2 周启动 |
| 24h 窗口理解偏差导致发送失败 | 状态机单测全覆盖；窗口外一律模板降级，不硬发 |
| Token 泄漏 | 系统用户长期 Token + Vault + 最小权限（仅 whatsapp_business_messaging 等） |
| 平台政策收紧（自动回复） | 自动回复仅限已注册 Skill + 人审兜底 + 用户可退订（STOP 关键词） |
| 成本失控 | 会话级预算护栏（budget_guard 复用）；营销会话默认人审 |
| GoodJob GPL 污染 | **零复制其代码**，仅思想借鉴；评审时逐文件核对来源 |

## 许可证合规说明
- GoodJob 主体 Apache-2.0：借鉴其**架构思想**无需额外义务；若未来直接采用其任何 Apache 代码，需保留版权声明与 NOTICE。
- `whatsapp-plugin` 为 **GPL-3.0-only**：本规划明确**不复制、不改写、不链接**其任何代码；"参考"仅限阅读层面的设计概念（会话隔离/幂等/检查中心），落地代码全部原创并用 Apache-2.0/MIT 兼容方式归入优丁代码库。
- Meta 侧：遵守 WhatsApp Business Policy（禁止未授权群发、必须支持退订、内容类别合规）。

---

## 附：一句话结论

GoodJob 强在"通道做得细"，优丁强在"编排做得深"。本方案把通道按 Meta 官方 API 用 Python 重写为 Execution Plane 的 Channel Adapter（吸收其会话隔离/幂等/证据设计），把每一条消息都交给 Control Plane 的意图引擎与经验飞轮处置——**通道是别人的好，大脑必须是我们自己的。**

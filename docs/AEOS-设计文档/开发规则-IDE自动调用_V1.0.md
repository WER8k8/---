# 开发规则 —— IDE 自动调用（V1.0）

> **生成时间**：2026-09-03（GMT+8）
> **适用范围**：所有 AI Agent（Claude / Trae / Qoder / Codex / Cursor 等）在使用 IDE 类工具进行 AI Global Growth OS 项目的开发工作时
> **配套文档**：《顺势开发导航索引.md》（中央索引）、《AI_Global_Growth_OS_统一架构与整合总纲_V1.0.md》（设计真相源）、《开发交接记录-轮16至轮22_R23断点.md》（操作手册）
> **版本**：V1.0（首发）

---

## 〇、规则原文（用户授权）

> 所有开发人员（即 AI Agent）在使用编程 IDE 进行开发工作时，必须配置并启用 IDE 的自动调用功能，确保 IDE 能够根据当前开发场景和任务需求，主动识别并调用相应的开发工具和技能包。鉴于开发过程中涉及的技能和工具种类繁多，人工记忆和手动调用效率低下且易出错，IDE 需具备自主调取和智能判断能力。具体实施要求包括：
> 1) 建立开发工具与技能包的分类索引系统；
> 2) 实现基于代码上下文和开发任务的智能识别机制；
> 3) 明确界定技能调用与 MCP（Model Context Protocol）调用的触发条件和使用场景，确保在不同开发阶段能够精准匹配并调用最适合的工具或程序。

---

## 一、规则核心要点

| 编号 | 要点 | 说明 |
|------|------|------|
| R-IDEA-1 | **必须开启 IDE 自动调用** | 所有 AI Agent 必须开启"auto tool use / auto skill use"开关，不得关闭 |
| R-IDEA-2 | **不得依赖人工记忆** | Skill / MCP 列表 ≥ 数十项，人工记忆不可靠，必须由 IDE 自动加载 |
| R-IDEA-3 | **三方分离原则** | 工具（Tool）/ 技能（Skill）/ MCP 必须分类索引、各自隔离、不可混用 |
| R-IDEA-4 | **上下文驱动** | 调用必须基于代码上下文或任务关键词，不得盲调 |
| R-IDEA-5 | **阶段对齐** | 不同开发阶段（设计/编码/调试/部署）限定可用 Skill/MCP 子集 |
| R-IDEA-6 | **失败回退有据** | 调用失败必须记录原因、不得静默重试超过 3 次 |
| R-IDEA-7 | **审计可追** | 每次调用必须写入 Trace（接入 `app/services/trace/trace_service.py`） |
| R-IDEA-8 | **MCP 仅远端** | MCP 只用于跨进程/跨服务调用；本地工具统一走 Skill |
| R-IDEA-9 | **副作用分级** | 写操作（fill/click/submit/publish/rotate）必经 Policy 闸门（`app/services/policy/engine.py`） |
| R-IDEA-10 | **零回归纪律** | 调用失败或降级不得阻断主链路（best-effort，吞异常 + 落 Evidence） |

---

## 二、术语界定（避免混用）

| 术语 | 严格定义 | 与本项目对应实现 |
|------|----------|------------------|
| **Tool**（工具） | IDE 内置原子能力（读写文件、执行命令、搜索等） | `read_file` / `write_file` / `run_command` 等 |
| **Skill**（技能） | 本地、可组合、单步或编排的领域能力，**无远程副作用** | `.trae-cn/skills/`、`_external/goodjob-crm/agent-skills/`、项目 `.workbuddy/memory/` |
| **MCP**（Model Context Protocol） | 远端进程或服务的标准协议调用，**有跨进程副作用** | `c:\Users\...\mcp\...` 下的 mcp_file_system / mcp_Computer_Use / mcp_plugin_* |
| **Plugin**（插件） | IDE 增强能力，通常通过 Skill 或 MCP 暴露 | `trae-remote-official:*` 插件族 |
| **Workflow**（工作流） | 多 Skill/MCP 编排的复合任务 | DeerFlow / Hermes / n8n |

---

## 三、分类索引系统（R-IDEA-1 实施要求）

### 3.1 索引文件位置

| 索引类型 | 路径 | 维护者 |
|----------|------|--------|
| 全局 Skill 索引 | `C:\Users\Administrator.WIN-36O2UQRI3U1\.trae-cn\work\6a97e015ec9d9803e14f75ac\SKILLS_INDEX.md`（待建） | AI Agent 启动时自动生成 |
| 全局 MCP 索引 | `C:\Users\Administrator.WIN-36O2UQRI3U1\.trae-cn\mcp\SERVERS_INDEX.md`（待建） | AI Agent 启动时自动生成 |
| 项目级 Skill 索引 | `上线网站开发完成\docs\SKILLS_INDEX.md`（待建） | 接入时自动追加 |
| 项目级 MCP 索引 | `上线网站开发完成\docs\MCP_SERVERS_INDEX.md`（待建） | 接入时自动追加 |

### 3.2 索引条目最小集

每个 Skill 条目必须包含：

```yaml
- name: html-deck                          # 唯一标识
  description: "创建动画丰富的 HTML 幻灯片"   # 一句话功能
  triggers:                                  # 触发关键词（用于自动匹配）
    - "做PPT"
    - "演示文稿"
    - "slides"
  stage: [design, presentation]              # 适用开发阶段
  fallback: html-report                      # 失败回退到哪个
  side_effect: none                          # 副作用分级
  trace_required: false                      # 是否必须写 Trace
  last_used: 2026-09-03                      # 最近使用
  hit_rate: 0.0                              # 命中率（用于自动降权）
```

每个 MCP 条目必须包含：

```yaml
- server: mcp_file_system
  description: "本地文件读写"
  triggers: ["读写文件", "查找项目", "写交接记录"]
  network: false                             # 是否跨网络
  side_effect: filesystem                    # 副作用范围
  trace_required: true
  auth_required: false
```

---

## 四、智能识别机制（R-IDEA-2 实施要求）

### 4.1 识别三要素

AI Agent 启用自动调用时，**必须**按以下顺序识别：

```
┌─ 1. 代码上下文（Context）
│     ├─ 当前文件路径 / 扩展名 / import 语句
│     ├─ 当前文件中的类名 / 函数名 / 关键字
│     └─ 最近 50 行代码片段
│
├─ 2. 任务描述（Intent）
│     ├─ 用户 Prompt 的关键词命中
│     ├─ 当前会话的阶段（前缀"修复"/"开发"/"查询"等）
│     └─ 最近 3 轮对话主题
│
└─ 3. 历史命中率（History）
      ├─ 同类任务历史调用记录
      └─ 失败技能自动降权
```

### 4.2 识别决策流程

```
用户输入 Prompt
    │
    ▼
提取意图关键词 ──→ 命中触发词表 ──→ 候选 Skill/MCP 集合
    │                                       │
    │                                       ▼
    │                                  代码上下文二次过滤
    │                                       │
    │                                       ▼
    │                                  阶段白名单过滤
    │                                       │
    │                                       ▼
    │                                  命中率排序
    │                                       │
    │                                       ▼
    └────────────────────────────────→ 调用优先级队列
                                            │
                                            ▼
                                    依次尝试（≤3 次）
                                            │
                            ┌───────────────┼───────────────┐
                            ▼               ▼               ▼
                        成功返回         失败重试        失败回退
```

### 4.3 上下文驱动示例

| 场景 | 代码上下文 | 任务关键词 | 自动调用 |
|------|------------|------------|----------|
| 改 `app/services/policy/engine.py` | `policy` + `engine` | "增加人审规则" | `code-review` Skill |
| 写 `tests/xxx_verify.py` | `tests/` + `verify` | "加个测试" | `tdd` Skill |
| 修前端组件 | `.tsx` / `.vue` | "样式不对" | `frontend-design` Skill |
| 调 Stripe | `stripe` import | "接入支付" | `mcp_plugin_*stripe*` |
| 部署到 Cloudflare | `wrangler.toml` | "上线" | `trae-remote-official:cloudflare:wrangler` |

---

## 五、Skill 调用 vs MCP 调用的边界（R-IDEA-3 实施要求）

### 5.1 边界判定矩阵

| 维度 | Skill | MCP |
|------|-------|-----|
| **位置** | 本地（同进程内） | 远端（跨进程或跨网络） |
| **网络** | 无 | 有（HTTP / IPC / WebSocket） |
| **副作用** | 文件、内存、IDE 状态 | 数据库、外部服务、文件 |
| **典型耗时** | < 5 秒 | 1-60 秒 |
| **失败模式** | 立即返回错误 | 超时 / 断连 / 鉴权失败 |
| **是否需要审计** | 仅当有副作用 | **必须** |
| **是否写 Trace** | 按需 | **必须**（`trace_required: true`） |
| **是否需要 Policy** | 仅当副作用 ≥ MEDIUM | **必须**（`app/services/policy/engine.py`） |
| **并发数** | 高（无外部依赖） | 低（受远端配额限制） |
| **典型例子** | html-deck、tdd、code-review | mcp_file_system、mcp_Computer_Use、mcp_plugin_Cloudflare |

### 5.2 触发条件决策树

```
需要调用某个能力
    │
    ├─ 是否跨进程？
    │     ├─ 是 → MCP
    │     └─ 否 ↓
    │
    ├─ 是否需要网络？
    │     ├─ 是 → MCP
    │     └─ 否 ↓
    │
    ├─ 是否修改数据库/外部服务？
    │     ├─ 是 → MCP
    │     └─ 否 ↓
    │
    ├─ 是否是项目自定义复合任务（多步骤编排）？
    │     ├─ 是 → Skill
    │     └─ 否 ↓
    │
    └─ 是否本地原子操作（读文件、查代码、生成片段）？
          ├─ 是 → Skill
          └─ 否 → 拆解后再判断
```

### 5.3 反例（**禁止**的混用）

| 错误 | 后果 | 正确做法 |
|------|------|----------|
| 用 MCP 读本地 Markdown | 慢 + 不可靠 + 占 MCP 配额 | 用 Skill `read_file` |
| 用 Skill 直连 Stripe API | 无审计 + 无 Policy 闸门 | 用 MCP `mcp_plugin_*stripe*` |
| 用 MCP 改 `app/core/config.py` | 跨进程改文件不必要 | 用 Skill `search_replace` |
| 写文件后用 MCP 再读一次校验 | 浪费 MCP 配额 + 增加延迟 | Skill 一次完成 |

---

## 六、开发阶段与可用工具子集

| 开发阶段 | 典型任务 | 优先 Skill | 优先 MCP |
|----------|----------|------------|----------|
| **设计** | 画架构图、写总纲、画思维导图 | `architecture-diagram`、`brainstorming`、`html-report` | 无（纯本地） |
| **编码** | 写代码、改 Bug、加测试 | `code-review`、`tdd`、`frontend-design`、`shadcn` | `mcp_file_system`（必要时） |
| **调试** | 跑测试、看日志、查状态 | `diagnosing-bugs`、`webapp-testing` | `mcp_Computer_Use`（GUI 调试） |
| **测试** | 跑 e2e、Lighthouse 审计 | `webapp-testing`、`lighthouse_audit` | `mcp_plugin_Chrome_DevTools_chrome-devtools` |
| **部署** | 部署到 Cloudflare / Pages | `cloudflare` 系列 | `mcp_plugin_Cloudflare_cloudflare-api` |
| **归档** | 写交接记录、整理文档 | `doc-writing-guide`、`docx`、`pdf` | 无 |
| **运维** | 监控、日志、告警 | `cloudflare:web-perf` | `mcp_plugin_Cloudflare_cloudflare-api` |

---

## 七、调用失败的回退策略

### 7.1 失败分类

| 错误码 | 含义 | 处理 |
|--------|------|------|
| `TIMEOUT` | 超时 | 重试 1 次，仍超时走回退 |
| `AUTH_DENIED` | 鉴权失败 | 不重试，提示用户重新授权（`RequestAuthorization`） |
| `NOT_FOUND` | 资源不存在 | 不重试，提示用户提供正确路径 |
| `RATE_LIMIT` | 限流 | 等待 60s 后重试 1 次 |
| `POLICY_DENIED` | Policy 拒绝 | 不重试，落 Evidence + 提示 |
| `EXEC_RUNTIME_ERROR` | 运行时错误 | 重试 1 次，仍失败走回退 |
| `BROWSER_RUNTIME_DISABLED` | 开关未开 | 不重试，提示用户开开关 |
| `IMPORT_ERROR` | 依赖未装 | 提示安装命令（如 `pip install playwright && playwright install chromium`） |

### 7.2 回退链路

```
首选 Skill/MCP
    │ 失败
    ▼
fallback 列表（按索引 `fallback` 字段）
    │ 也失败
    ▼
通用工具（read_file / grep 等原子能力）
    │ 也失败
    ▼
明确告知用户失败原因，**不**继续盲调
```

### 7.3 重试纪律

- **最多重试 3 次**（含首次）
- **总耗时 ≤ 60 秒**（含等待）
- **失败后必须落 Trace**（即使调用本身未启动 trace）
- **不得静默重试**——每次重试必须更新 `metadata.retry_count`

---

## 八、Trace 接入规范（R-IDEA-7 实施要求）

每次 IDE 自动调用**必须**按以下规则写 Trace：

### 8.1 必须写 Trace 的情况

- 调用 MCP 服务器
- 调用任何写操作 Skill（fill/click/submit/publish/rotate）
- 调用失败或降级
- 跨租户调用

### 8.2 写入方式

通过项目内 `app/services/trace/trace_service.py`：

```python
from app.services.trace.trace_service import start_trace, complete_trace

with start_trace(action="skill.html-deck", tenant_id=...) as t:
    result = invoke_skill(...)
    complete_trace(t, status="success", result=result)
```

### 8.3 字段最小集

```
trace_id:         UUID
agent:            AI Agent 名（claude-sonnet / trae-cn / ...）
caller:           用户标识
skill_or_mcp:     名称
action:           具体动作
context:          调用上下文（去敏感）
result:           成功/失败 + 摘要
duration_ms:      耗时
retry_count:      重试次数
fallback_used:    走了哪个回退
```

---

## 九、Policy 闸门接入规范（R-IDEA-9 实施要求）

涉及以下动作时，**必须**先走 Policy 闸门：

| 动作类型 | Policy 检查项 | 失败处理 |
|----------|---------------|----------|
| **写文件**（IDE 自动写） | 不在白名单路径内拒绝 | 落 `policy_verdict=denied` + 不写 |
| **执行命令**（`run_command`） | 阻断 `rm -rf` / `format` / 删盘 | 同上 |
| **MCP 写操作** | `app/services/policy/engine.py` 四维判定 | 落 Evidence + 不执行 |
| **Skill 写动作** | 同 MCP | 同上 |
| **跨租户调用** | tenant_id 白名单 | 阻断 |

### 9.1 红线（不可违反）

- R5：**永不入树** GoodJob whatsapp-plugin（GPL-3.0）
- R9：**访客输入不可信**——LLM 层隔离 + 限长截断 + brand_guard 净化
- R-IDEA-NEW-1：**写操作必须走 Policy**——IDE 不得绕过 policy 直接写入业务表
- R-IDEA-NEW-2：**失败不得阻断主链路**——Trace + Evidence 必落，调用方不感知

---

## 十、本项目特殊点

### 10.1 已就位的能力（截至 2026-09-03）

| 类别 | 数量 | 路径 |
|------|------|------|
| Skills | 100+ | `available_skills` 列表 |
| MCP 服务器 | 5 | mcp_file_system / mcp_Computer_Use / mcp_plugin_Chrome_DevTools / mcp_plugin_Cloudflare / mcp_Cloudflare_cloudflare-api |
| 项目已验证 | 503 / 0 FAIL | 10 套测试（write 57、real 30、skeleton 60、paperclip 32、caller 30、chain 71、trace 37、meter 33、registry 91、vault 62） |

### 10.2 启用清单（按 IDE）

| IDE | 自动调用开关 | Skill 注册目录 | MCP 配置目录 |
|-----|--------------|----------------|--------------|
| Trae CN | 默认开 | `~/.trae-cn/work/*/skills` | `~/.trae-cn/mcp/` |
| Qoder CN | 手动开 | `.qoder/skills/` | `.qoder/mcp/` |
| Claude Code | `--auto-approve` | `.claude/skills/` | `.claude/mcp/` |
| Cursor | "Composer" 模式 | `.cursor/skills/` | `.cursor/mcp/` |

### 10.3 禁止清单

- ❌ 用 Skill 直连外部 API（必须走 MCP）
- ❌ 绕过 Policy 闸门写业务表
- ❌ 关闭 IDE 自动调用开关"为了省事"
- ❌ 把 API Key 写入 Prompt（必须经 MCP 鉴权）
- ❌ 静默重试超过 3 次

---

## 十一、版本与变更

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| V1.0 | 2026-09-03 | 首发：基于用户授权的 IDE 自动调用规则原文，配套 Skill/MCP 边界矩阵 | WorkBuddy |

---

## 十二、附：Skill/MCP 速查表（节选）

### 12.1 常用 Skill（前 20 高频）

| Skill 名 | 触发关键词 | 阶段 |
|----------|------------|------|
| `html-deck` | "做PPT"、"演示文稿" | 设计 |
| `html-report` | "研究报告"、"白皮书" | 设计 |
| `architecture-diagram` | "画架构图"、"系统图" | 设计 |
| `brainstorming` | "头脑风暴"、"需求分析" | 设计 |
| `frontend-design` | "前端美化"、"界面设计" | 编码 |
| `code-review` | "代码评审"、"code review" | 编码 |
| `tdd` | "测试驱动"、"先写测试" | 编码 |
| `shadcn` | "shadcn"、"组件库" | 编码 |
| `diagnosing-bugs` | "诊断"、"bug" | 调试 |
| `webapp-testing` | "E2E 测试" | 测试 |
| `dev-expert` | "咨询专家"、"技术选型" | 编码 |
| `doc-writing-guide` | "写文档"、"PRD" | 归档 |
| `docx` / `pdf` / `xlsx` | "Word"、"PDF"、"Excel" | 归档 |
| `cloudflare:wrangler` | "部署到 Cloudflare" | 部署 |
| `cloudflare:web-perf` | "性能分析" | 运维 |
| `alipay-payment-integration` | "接入支付宝" | 编码 |
| `export-business-assistant` | "外贸"、"开发信" | 编码 |
| `mcp-builder` | "MCP 服务器" | 编码 |
| `dogfood` | "找 bug"、"QA" | 调试 |
| `qa` | "反馈问题" | 调试 |

### 12.2 可用 MCP 服务器

| MCP 服务器 | 用途 | 副作用 |
|------------|------|--------|
| `mcp_file_system` | 本地文件读写 | filesystem |
| `mcp_Computer_Use` | 跨应用 GUI 操作 | 高（系统级） |
| `mcp_plugin_Chrome_DevTools_chrome-devtools` | Chrome 调试、性能审计 | browser |
| `mcp_plugin_Cloudflare_cloudflare-api` | Cloudflare 平台操作 | external API |
| `mcp_integrated_code_mode` | 受控 JS 代码执行 | runtime |

---

## 十三、关联索引（在导航索引中的位置）

本规则文档在《顺势开发导航索引.md》中的引用位置（待续写）：

```
顺势开发导航索引.md
└─ §X 开发规则：IDE 自动调用
   ├─ 引用本文件：docs/开发规则-IDE自动调用_V1.0.md
   ├─ 速查表（摘要）
   └─ 与红线 R5/R9 的交叉引用
```

---

**文件结束**

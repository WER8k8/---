# Trade AI Agent 适配器（app/services/adapters/tradeai）

> 总纲依据：§5.2（代码级嫁接裁决）、§1.2/1.3（冻结原则）、§8 迁移 082/083。

## 来源与许可证
- 来源：Trade AI Agent（Gitee: LBones-li/agent_trade_b）；代码副本位于工作区 `_external/trade-ai-agent/`。
- 许可证：README 声明 **MIT**，但根目录无 LICENSE 文件——**商用合入前必须向作者书面确认**（总纲 §9.4-1，未完成前不得对外分发含本适配器的版本）。
- 移植文件须保留出处注释（MIT 义务）。

## 桥接内容（连通性试验已验证）
| vendor 资产 | 暴露名 | 用途 |
|---|---|---|
| BaseSkill / SkillRegistry / SkillStatus | 同名 | 迁移 083 `skills` 表的运行时执行层 |
| WorkflowEngine / WorkflowDefinition / StepDefinition / StepCondition / ExecutionStatus / WorkflowExecution | 同名 | `ai_tasks`（082）子任务条件分支 + 暂停/恢复 |
| AgentOrchestrator | `tenant_orchestrator(tenant_id)` | Hermes 内层编排的可挂载执行器（按租户隔离实例） |
| ExecutionContext / MessageContext | `make_context(tenant_id, task_id, **inputs)` | 执行上下文（自动注入租户/任务标记） |

## 关键机制
1. **命名空间隔离**：双方顶层包都叫 `app`。本适配器加载时把 vendor 模块改名到 `tradeai_vendor.app.*`（换出→载入→改名→还原→移除路径），优丁 `app` 零污染（验证：_adapter_test 第 5 项）。
2. **租户隔离**：唯一入口是 `tenant_orchestrator()` / `make_context()`；tenant_id 强制非空并写入上下文状态袋。
3. **不持有状态**：任务真相归 `ai_tasks`，本层只做执行；接入时必须把执行结果回写 `ai_tasks` 并按 §6 走双关卡。

## 环境变量
| 变量 | 必需 | 说明 |
|---|---|---|
| `TRADEAI_SECRET_KEY` | 生产必需 | 未设置时使用开发占位值并告警（总纲 §7.7 密钥纪律） |
| `TRADEAI_BACKEND_PATH` | 可选 | 覆盖 `_external/trade-ai-agent/backend` 的默认推导路径 |
| `CREDENTIAL_ENCRYPTION_KEY` | 建议 | vendor 凭证加密（Fernet）；未设时 vendor 侧警告明文 |

## 已知限制（接线前必读）
1. **惰性导入风险（4 处，已扫描定位）**：`encryption.py:20`、`event_bus.py:5`、`notification_handlers.py:109`、`security.py:66` 存在函数级 `from app.*`——运行时若触发会命中优丁 `app` 而失败。核心三件套不触碰这些路径；**不要**启用 vendor 的消息循环/通知/认证功能（认证本就不引入，§5.2.3）。
2. vendor `ExecutionContext` 无 `get_input` 读取器：输入经 `set_input` 写入、以状态袋/输出侧读取。
3. 本适配器**尚未被任何路由/服务 import**（零回归）；正式接线任务 = 总纲 §9.4 后续项（ai_tasks 执行器对接）。

## 验证记录
- `.workbuddy/_compat_report.txt`：AST 86/86、14 表清点、Node 环境
- `.workbuddy/_compat_report2.txt`：SECRET_KEY 后三件套导入成功、枚举值与设计吻合
- `.workbuddy/_adapter_test.txt`：隔离加载/租户工厂/导出/优丁完整性 全通过

# 第三方源码并入说明

以下模块自开源项目 **改编** 并入 `backend/app/services/foreign_trade/`，遵循各项目许可证；**未**整仓 fork，亦未包含 SMTP 群发/社媒爬虫账号池代码。

| 模块 | 来源 | 许可证 | 路径 |
|------|------|--------|------|
| OSINT 六层背调 | [chefroger/smart-trade-ai](https://github.com/chefroger/smart-trade-ai) | MIT | `osint/` |
| 官网 ICP 分析 | [qingchuh/sale_agent_factory](https://github.com/qingchuh/sale_agent_factory) | MIT | `website_icp_service.py` |
| 潜客清洗 | [EricHong123/Eric_Frank](https://github.com/EricHong123/Eric_Frank) | 见上游 | `prospect_cleaner_service.py` |
| PI/报价 Markdown | smart-trade-ai 商务文档 playbook | MIT | `trade_document_service.py` |

**刻意未并入：**

- Eric_Frank / AI_Find_Customer 的 SMTP 自动发送与 campaign scheduler
- Eric_Frank skill_social_scraper（反爬/账号池）
- nana-crm / open-erp 整仓（仅字段/playbook 参考，见 catalog）

**可选依赖：** `holehe`（OSINT Layer1 邮箱注册检测）；未安装时 Layer1 自动跳过。

## 智能体编排（本仓）

| 入口 | 技能 ID | 说明 |
|------|---------|------|
| `ubrain/chat` intent | `osint_check` / `website_icp` / `proforma_invoice` / `prospect_clean` | UBrain 意图路由 |
| `foreign_trade_agent_service.py` | 统一 `agent_envelope` | DeerFlow / 飞轮 / onboarding 共用 |
| `flywheel_workflow` | 找客后 `enrich_buyers_with_clean_and_osint` | 卖货飞轮自动清洗+背调 |
| `onboarding_autopilot` | 建站后 `run_website_icp_agent` | TTV 写入租户记忆 |

REST Admin API（`/foreign-trade/*`）与 UBrain 共用底层 service，编排门面优先走 `foreign_trade_agent_service`。

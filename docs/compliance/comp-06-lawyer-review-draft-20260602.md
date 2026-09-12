# COMP-06 · 律师/合规复审申请表（草稿已填）

| 字段 | 内容 |
|------|------|
| 软件名称 | 优丁建材 AI-SaaS 智能营销平台 V2.0 |
| 版本 | V2.0 |
| 申请类型 | 计算机软件著作权登记 ×2 |
| 代码来源 | 自研 + 开源组件（见 `docs/compliance/OPEN-SOURCE-NOTICES.md`） |
| 禁止提交 | 见 `docs/compliance/ip-02-forbidden-list.md` |
| AI 生成声明 | 说明书 COMP-03 由经办人手写；核心代码为团队自研，AI 仅辅助片段 |
| 附件 | `comp-evidence-bundle.json` · `docs/compliance/rz-60-pages/`（60 页）· cert 截图 12 PNG |
| 导出校验 | `scripts/validate-be-06-export.py` → ok: true（2026-06-02） |
| 范围扫描 | COMP-07 PASS · `scripts/validate-patent-copyright-scope.py` |

## 自研范围说明（摘要）

- **后端**：FastAPI BFF（`admin_bff/`）、询盘统一服务、Plan Gate、UBrain 审计
- **前端**：Vben 壳 + `youding-admin-kit` + Formily site-editor 试点
- **不含**：整库 `_ref/` 克隆源码作为登记材料；仅自研目录内 60 页

## 律师意见栏

| 项 | 意见 | 签字 |
|----|------|------|
| 开源合规 | （待填） | |
| 权利归属 | （待填） | |
| 与专利冲突 | 参考 PAT-02 memo | |
| 材料完整性 | rz-60 + 门禁 JSON | |

**经办日期**：2026-06-02 · **状态**：草稿待律师签字（S2 COMP-06 正式提交）

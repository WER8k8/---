# IP-01 · RZ + PAT 材料边界统筹

> **W1 定稿** · 对照 [`open-source-audit/00-repo-link-inventory.md`](./open-source-audit/00-repo-link-inventory.md)

## 可登记（软著 / 专利实施例）

| 范围 | 路径 |
|------|------|
| Admin BFF UAC | `backend/app/api/v1/admin_bff/` |
| 自研业务服务 | `backend/app/services/`（含 AI 调度） |
| 四壳 + kit | `frontend/admin/src/views/{client,agent,admin}` · `components/youding/` |
| Stub/送检矩阵 | `frontend/admin/src/constants/stubVisibility.ts` |

## 明确排除

| 范围 | 原因 |
|------|------|
| `frontend/admin-vben/**` | Vue Vben 开源壳 |
| `_ref/**` | 审计用克隆，非自研 |
| Stub 实验室页源码 | 未上线 / 演示 |
| Naive/RuoYi 整库 | 第三方 |

## 专利 vs 软著

| 轨道 | 核心 |
|------|------|
| **专利** | 多模型调度算法 + 配额 + 失败切换（交底书） |
| **软著②** | BFF + 租户业务 API + kit UI |

**冲突复核**：PAT-06 / COMP-07 @ S2

- [x] IP-01 边界 v1  
- [ ] IP-02 60 页禁止清单签字（W2）

*IP-01 v1*

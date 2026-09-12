# 如何用 ECC（222 人）开「视频云存储」评审会

> 给发起人：你不需要懂技术，在 Cursor 里**发一条消息**即可触发多角色讨论。

---

## 一键触发（复制到 Cursor 对话）

```text
请按 .project/workflows/media-factory-storage-review.yaml 开 ECC 评审会：
- 先 python scripts/agency-launch.py
- 并行委派：Agents Orchestrator、Product Manager、Software Architect、Backend Architect、DevOps Automator、ECC security-reviewer
- 会前材料：docs/MEDIA-FACTORY-STORAGE-DECISION.md、docs/MEDIA-FACTORY-CLOUD-STORAGE.md
- 会后把汇总写入 docs/meetings/MEDIA-FACTORY-STORAGE-ECC-MINUTES.md
```

---

## 会前准备

```powershell
cd "c:\Users\97907\Desktop\上线网站"
python scripts/agency-launch.py
```

确认输出里 **Agency 184 + ECC 38** 已扫描到。

---

## 参会角色（本议题相关 subset）

| 角色 | 来源 | 职责 |
|------|------|------|
| Agents Orchestrator | Agency | 议程、节奏、汇总 |
| Product Manager | Agency | 四项拍板、产品待办 |
| Software Architect | Agency | 双轨架构是否成立 |
| Backend Architect | Agency | 代码/任务/估时 |
| DevOps Automator | Agency | 密钥、环境、监控 |
| security-reviewer | ECC | 预签名、租户、密钥 |

其余 200+ 角色**本议题不参会**（避免全栈空转）。若需营销/法务，另开议题。

---

## 工作流文件

- 仓库内（可入库）：`.project/workflows/media-factory-storage-review.yaml`
- 全量 7 阶段开发流（参考）：`UJ/website CodeBuddy/workflows/agency-ecc-full.yaml`

---

## 产出物

| 文件 | 说明 |
|------|------|
| `docs/meetings/MEDIA-FACTORY-STORAGE-ECC-MINUTES.md` | AI 会后纪要（主交付） |
| `docs/MEDIA-FACTORY-STORAGE-DECISION.md` | 已定决策（会前读） |

---

## 与「真人开会」的区别

- ECC 会是**异步多 Agent 评审**，适合技术对齐与纪要；**账号开通、合同、预算**仍需真人 PM/运维执行。
- 豆包 CloudBase/MinIO 主 CDN 方案已在决策文档中**否决**，会上不重复辩论，除非 PM 提出新证据。

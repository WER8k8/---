# ECC 评审会纪要 · 视频云存储（酷播 + R2）

> **会议类型**：Agency + ECC 多角色评审（非真人会议）  
> **日期**：2026-05-31  
> **议题**：多媒体工厂视频上云双轨方案是否可执行  
> **工作流**：`.project/workflows/media-factory-storage-review.yaml`  
> **会前材料**：[MEDIA-FACTORY-STORAGE-DECISION.md](../MEDIA-FACTORY-STORAGE-DECISION.md)

---

## 参会角色（本议题 subset）

| 角色 | 部门 | 发言摘要 |
|------|------|----------|
| Agents Orchestrator | 编排 | 议程控制，确认不跑全 7 阶段实现流 |
| Product Manager | 产品部 | 同意选型，明确四项拍板 |
| Software Architect | 工程技术部 | 架构通过，有条件项 2 条 |
| Backend Architect | 工程技术部 | 代码已接 P1/P2，P0/P3 待排期 |
| DevOps Automator | 工程技术部 | 密钥与验证清单 |
| security-reviewer (ECC) | 工程门控 | 有条件上线 |

> 说明：222 人中**仅上表 6 角色**参与本议题；其余角色不召集，避免空转。

---

## 一、会议结论（全员同意）

1. **选型维持**：国内 **酷播云** + 海外 **R2** + 可选棱束链备份；**不采纳**豆包 CloudBase / MinIO 客户主 CDN / 独立 `/api/video/upload` Demo。  
2. **体验目标**：渲染 `done` 后**本地立即可预览**；上云后台并行，不挡 API。  
3. **代码状态**：`media_cloud_upload_service` 等已落地；**差配置与 P0/P3 业务闭环**。  
4. **下一步**：运维填密钥 → 后端 P0 验收一条端到端 → PM 核对对外保留期文案。

---

## 二、四项拍板（Product Manager 提议 → 技术无异议）

| # | 问题 | 决议 |
|---|------|------|
| 1 | 酷播免费档是否够试点？ | **先试用酷播免费档**；3 个月后由 PM 根据存储/流量账单复盘；不足再评估七牛（P5），不提前开发 |
| 2 | R2 是否本期绑自定义域名？ | **本期不做**；用预签名 URL + `publish_video_url`；域名/CDN 列入 backlog |
| 3 | 成品保留 72h + handoff 删文件是否与承诺一致？ | **PM 需在帮助中心/合同核对**；技术默认 72h（`MEDIA_RETENTION_HOURS`），若商务承诺更长则改配置并同步文案 |
| 4 | 是否每任务酷播+R2 双写？ | **是**（当前实现）；不按租户拆存储，除非 PM 后续提合规分区需求 |

---

## 三、分角色意见摘录

### Software Architect

- **结论**：有条件通过。  
- **优点**：职责清晰（酷播=国内播放，R2=海外拉源）；与 Egress 发布模型一致。  
- **风险**：双云依赖运维配钥；酷播转码耗时导致 `cloud_upload_status=uploading` 时间较长。  
- **MUST-FIX**：生产环境禁止把 writetoken/secretkey 写入已跟踪文件；R2 预签名需可配置缩短时效用于敏感内容（后续）。  
- **反对 MinIO 主 CDN**：无全国 CDN 与转码，单点带宽。  
- **反对 CloudBase 豆包 Demo**：SDK 不可信，与现流水线重复。

### Backend Architect

- **P0 估时**：配密钥 + 跑通 1 条上云 ≈ **0.5–1 人天**；`guest_token` 注册绑定 ≈ **1–2 人天**。  
- **P3 估时**：SEO 发布带 `publish_video_url` ≈ **1–2 人天**。  
- **表字段**：当前够用；`guest_token` 列已预留。  
- **测试**：Mock 渲染 → `skipped`；配钥后 `done/partial`；海外发布用 R2 URL 拉取一次。  
- **认可** `skipped` 时本地 `preview_url`，不挡演示。

### DevOps Automator（检查清单）

- [ ] 酷播 v4 开通，writetoken/secretkey/userid 写入**服务器** `.env`  
- [ ] Cloudflare R2 Bucket + API Token，写入 `MEDIA_R2_*`  
- [ ] 确认 `MEDIA_CLOUD_UPLOAD_ENABLED=true`  
- [ ] 重启后端，提交 1 条渲染，查 `cloud_upload_status`  
- [ ] 日志无密钥明文；git 无 `.env` 提交  
- [ ] 预签名 URL 在测试环境可播、可下载  
- [ ] 监控：上云失败率、`partial` 比例（可先日志）  
- [ ] 备份：棱束链 P4 可选，本期不阻塞上线  

### ECC security-reviewer

- **结论**：有条件上线。  
- **MUST-FIX**：生产密钥仅环境变量；管理后台播放外链需 HTTPS。  
- **SHOULD-FIX**：缩短对外暴露的 R2 预签名默认 7 天（按发布任务生命周期生成）；审计 `guest_token` 绑定防越权。

---

## 四、分工与截止日期（请 PM 填日期）

| 事项 | 负责 | 截止 |
|------|------|------|
| 开通酷播 + R2，密钥交运维 | PM/运营 | ____ |
| 服务器 `.env` 配置与重启 | 运维 | ____ |
| 跑通 P0 端到端演示 | 后端 | ____ |
| `guest_token` 绑定 API | 后端 | ____ |
| 帮助中心保留期文案核对 | PM/法务 | ____ |
| P3 发布打通 `publish_video_url` | 后端 | ____ |

---

## 五、创始人只需知道

- **不用换方案**，ECC 产品+技术一致：就酷播 + R2。  
- **你要做的**：让 PM 去开账号、定对外「视频保存多久」的说法。  
- **技术已写好大部分**，配好密钥就能试；豆包那三套不用管。

---

## 六、下次 ECC 同步验收标准

- 测试环境一条任务：`raw_status=done` 且 `cloud_upload_status=done` 或 `partial`  
- `preview_url` 为酷播或 R2 地址（非仅本地）  
- 会议纪要四项拍板已填入第四节日期  

---

*本纪要由主编排 Agent 根据已定决策文档与代码现状合成；若需重新跑并行子代理，在 Cursor 发送 [MEDIA-FACTORY-STORAGE-ECC-RUNBOOK.md](./MEDIA-FACTORY-STORAGE-ECC-RUNBOOK.md) 中的一键触发语。*

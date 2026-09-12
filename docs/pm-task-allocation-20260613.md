# PM 任务分配表 · Sprint-COMM-1（鉴定面商用 W1）

> **签发**：ECC 产品经理 **PM-07**  
> **生效**：2026-06-13  
> **性质**：**本 Sprint 唯一调度依据** — 蜂群按 Lane 并行，standup 只报任务 ID  
> **总纲**：[`商用上线-跨部门作战图-2026-06-13.md`](./商用上线-跨部门作战图-2026-06-13.md)  
> **机器可读**：[`pm-dispatch-latest.json`](./pm-dispatch-latest.json)  
> **宪章**：[`pm-swarm-parallel-charter.md`](./pm-swarm-parallel-charter.md)

---

## 一、Sprint 目标（W1）

| 项 | 内容 |
|----|------|
| **代号** | COMM-1 · 鉴定面商用 · 阶段 1 第 1 周 |
| **目标** | 五门禁中 **G2/G3 先止血**；Owner 阻塞单列催办；**不扩实验室** |
| **退出** | `cert:gate` 绿 · dev 栈双绿 · preflight 无 required fail · PM 催 O-1 有排期 |

---

## 二、站会优先序（今日 FAIL Lane 先修）

> 来源：`docs/ops/expert-standup-latest.md`（2026-06-13，1/7 通过）

| 优先 | 任务 ID | Lane | 主责 | 交付 |
|------|---------|------|------|------|
| P0 | **COMM-SRE-01** | SRE | SRE | `start-dev-admin` 登录代理双绿 |
| P0 | **COMM-QA-01** | F→B | QA 开单 / 前端修 | `npm run cert:gate` 绿 |
| P0 | **COMM-BE-01** | E | 后端 | `run_production_preflight` required 无 fail |
| P0 | **COMM-BE-02** | E | 后端 | `check_mounted_routes.py` 绿 |
| P0 | **COMM-BE-03** | E | 后端+安全 | Webhook 验签 Lane 绿 |
| P1 | **COMM-ARCH-02** | A | 架构 | staging preflight `ok: true` |
| P1 | **COMM-GR-01** | GR | 后端 | greedy_readiness 单测绿 |
| — | **COMM-PM-02** | H | PM-07 | Owner O-1~O-3 催办记录 |

**硬规则**：QA Lane **不修功能** — 开单给 E/B/SRE，带任务 ID。

---

## 三、蜂群泳道 · 并行分配（COMM-1）

| Lane | 主责 | 本周任务 ID | 并行 | Out-of-Scope |
|------|------|-------------|------|--------------|
| **H** | PM-07 | COMM-PM-01~03 | ✅ | 不写实现代码 |
| **PD** | 产品经理 | COMM-PD-01~03 | ✅ | 不派研发 Kill 前改路由 |
| **A** | 架构 | COMM-ARCH-01~02 | ✅ | 不改 Vue 业务页 |
| **F** | QA | COMM-QA-01~03 | ✅ | 不修功能逻辑 |
| **E** | 后端 | COMM-BE-01~03 | ✅ | 不改 Admin UI |
| **B** | 前端 | COMM-FE-01~02 | ✅ | 不扩全局路由 |
| **SRE** | SRE | COMM-SRE-01 | ✅ | — |
| **GR** | 后端 | COMM-GR-01 | ✅ | 不宣称全引擎 GEO |
| **VIS/UX** | 设计 | COMM-VIS-01, COMM-UX-01 | ✅ | BJ-NAV-04 待 JD-01 |
| **APP** | 出海计 | COMM-APP-01 | ✅ | AAB 待商店五图 |

**依赖仅 2 条**：

1. `COMM-FE-02` 待 `COMM-PD-03` 话术签字  
2. `COMM-QA-02` 三张截图待 **O-1 HTTPS 域**（无则标 `blocked`）

其余 Lane **默认同时开工**。

---

## 四、任务明细

### Lane H · PM-07

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-PM-01 | 签发本分配表 + JSON | 6/13 | 本文 + `pm-dispatch-latest.json` |
| COMM-PM-02 | Owner O-1~O-3 催办 | 6/16 | `owner-review` 更新 |
| COMM-PM-03 | Stub Kill 评审会 | 6/18 | `stub-matrix-T-PM-02-v1.json` |

### Lane PD · 产品

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-PD-01 | 送检清单签字跟进 | 6/17 | `送检功能清单-v1.md` 签字页 |
| COMM-PD-02 | Stub 矩阵草案 v1 | 6/18 | 24 组前缀 Kill/Lab/Gate |
| COMM-PD-03 | SEO 对外话术一页 | 6/20 | 摘自信任图 |

### Lane A · 架构

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-ARCH-01 | HTTPS 演示域技术清单 | 6/16 | `DEMO_HTTPS_DOMAIN` runbook |
| COMM-ARCH-02 | staging preflight 0 fail | 6/14 | `staging-preflight-auto-latest.json` |

### Lane F · QA

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-QA-01 | cert:gate 修红 | 6/14 | 门禁绿 |
| COMM-QA-02 | 七步⑤ 三张截图 | 6/17 | `screenshots/round2/` |
| COMM-QA-03 | 12 模块截图分工 | 6/16 | 分工表 |

### Lane E · 后端

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-BE-01 | backend_preflight Lane | 6/14 | preflight JSON |
| COMM-BE-02 | security_routes Lane | 6/14 | 路由审计脚本 |
| COMM-BE-03 | webhook_security Lane | 6/15 | 验签单测 |

### Lane B · 前端

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-FE-01 | 超管工作台无假 KPI 复核 | 6/13 | `admin/index.vue` |
| COMM-FE-02 | SEO 示意页空态 | 6/19 | schema/eeat 标注 |

### Lane SRE

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-SRE-01 | dev 栈 login 500 | 6/14 | 双绿探针 |

### Lane GR · 搞钱大赛

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-GR-01 | greedy_readiness | 6/16 | hermes 单测 |

### Lane APP · 出海计

| ID | 任务 | 截止 | 交付物 |
|----|------|------|--------|
| COMM-APP-01 | PWA 四 Tab 验收清单 | 6/17 | tenant `/client/app` |

---

## 五、Owner 阻塞（PM 催办，非研发）

| ID | 事项 | 阻塞任务 |
|----|------|----------|
| O-1 | HTTPS 演示独立域 | MOD-01, MOD-04, COMM-QA-02 |
| O-2 | 询盘 IM 生产密钥 | MOD-02, ITER-03c |
| O-3 | 5+5 平台 + 套餐价签字 | MOD-03, MOD-08 |

---

## 六、站会话术（每日 30 分钟）

```
Sprint: COMM-1 W1
G1~G5: [各红绿灯]
昨日 FAIL Lane: [SRE/QA/BE…] → 任务 ID
今日并行 Lane: [列 ID，≤8 条]
Owner: O-1/O-2/O-3 状态
禁止: 无 ID 开工 / 实验室对外 / 假交付 P0>0
```

---

## 七、ECC 子代理委派建议

| 任务类型 | ECC Agent |
|----------|-----------|
| COMM-BE-* | `build-error-resolver` / `python-reviewer` |
| COMM-FE-* / COMM-QA-01 | `typescript-reviewer` / `e2e-runner` |
| COMM-ARCH-* | `architect` |
| COMM-PM-* | `planner` + `doc-updater` |
| 合并前 | `code-reviewer` + `validate-no-fake-delivery.py` |

启动：`python scripts/agency-launch.py`

---

*PM-07 签发 · Sprint-COMM-1 · 2026-06-13*

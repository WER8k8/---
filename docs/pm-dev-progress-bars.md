# 开发任务进度条（横向 · 仅未完成）

> **更新**：2026-06-04 · 数据源 [`pm-dev-task-progress.json`](./pm-dev-task-progress.json)
> **刷新**：`backend\.venv\Scripts\python.exe scripts/render-dev-progress-bars.py`

## 横向进度（预览）


<style>
.yd-progress-wrap { font-family: ui-sans-serif, system-ui, sans-serif; font-size: 13px; max-width: 100%; }
.yd-progress-row {
  display: flex; align-items: center; gap: 10px;
  margin: 8px 0; width: 100%; flex-wrap: nowrap;
}
.yd-progress-row .id { flex: 0 0 72px; font-weight: 600; color: #0f172a; }
.yd-progress-row .name { flex: 0 0 160px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.yd-progress-row .track {
  flex: 1 1 auto; min-width: 80px; height: 12px;
  background: #e2e8f0; border-radius: 6px; overflow: hidden;
}
.yd-progress-row .fill {
  height: 100%; border-radius: 6px;
  background: linear-gradient(90deg, #2563eb, #60a5fa);
}
.yd-progress-row .pct { flex: 0 0 44px; text-align: right; font-weight: 700; color: #1e40af; }
.yd-progress-row .owner { flex: 0 0 52px; font-size: 12px; color: #94a3b8; text-align: right; }
.yd-progress-summary {
  display: flex; align-items: center; gap: 10px; margin: 12px 0 4px;
  padding-top: 8px; border-top: 1px dashed #cbd5e1;
}
.yd-progress-summary .label { flex: 0 0 232px; font-weight: 600; color: #475569; }
.yd-progress-summary .track { flex: 1; height: 14px; background: #e2e8f0; border-radius: 7px; overflow: hidden; }
.yd-progress-summary .fill { height: 100%; background: linear-gradient(90deg, #059669, #34d399); border-radius: 7px; }
.yd-progress-summary .pct { flex: 0 0 44px; text-align: right; font-weight: 700; }
</style>

<div class="yd-progress-wrap">
<p><strong>Sprint-R1 研发攻坚 6/3–6/16</strong></p>
<div class="yd-progress-row"><span class="id">ARCH-04</span><span class="name">HTTPS + compose 实跑</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="pct">99%</span><span class="owner">架构</span></div>
<div class="yd-progress-row"><span class="id">QA-04</span><span class="name">Locust 冒烟→72h</span><div class="track"><div class="fill" style="width:96%"></div></div><span class="pct">96%</span><span class="owner">QA</span></div>
<div class="yd-progress-row"><span class="id">BJ-01</span><span class="name">Formily site-editor</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="pct">99%</span><span class="owner">前端</span></div>
<div class="yd-progress-row"><span class="id">PAT-02</span><span class="name">新颖性检索 memo</span><div class="track"><div class="fill" style="width:92%"></div></div><span class="pct">92%</span><span class="owner">IP/专利</span></div>
<div class="yd-progress-row"><span class="id">COMP-06</span><span class="name">律师复审表</span><div class="track"><div class="fill" style="width:93%"></div></div><span class="pct">93%</span><span class="owner">IP</span></div>
<div class="yd-progress-summary"><span class="label">平均 · 5 项未完成</span><div class="track"><div class="fill" style="width:95%"></div></div><span class="pct">95%</span></div>
<br/>
<p><strong>业务链缺口 MOD</strong></p>
<div class="yd-progress-row"><span class="id">MOD-01</span><span class="name">独立域/SSL 实机</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="pct">99%</span><span class="owner">架构</span></div>
<div class="yd-progress-row"><span class="id">MOD-02</span><span class="name">询盘 IM 生产密钥</span><div class="track"><div class="fill" style="width:98%"></div></div><span class="pct">98%</span><span class="owner">后端</span></div>
<div class="yd-progress-row"><span class="id">MOD-03</span><span class="name">40 平台 PM 签字</span><div class="track"><div class="fill" style="width:45%"></div></div><span class="pct">45%</span><span class="owner">PM</span></div>
<div class="yd-progress-row"><span class="id">MOD-04</span><span class="name">七步实机录屏</span><div class="track"><div class="fill" style="width:75%"></div></div><span class="pct">75%</span><span class="owner">QA</span></div>
<div class="yd-progress-row"><span class="id">MOD-06</span><span class="name">出海计 App 上架包</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="pct">99%</span><span class="owner">App</span></div>
<div class="yd-progress-row"><span class="id">MOD-07</span><span class="name">贸易情报矩阵签字</span><div class="track"><div class="fill" style="width:45%"></div></div><span class="pct">45%</span><span class="owner">PM</span></div>
<div class="yd-progress-row"><span class="id">MOD-08</span><span class="name">5+5 平台+HTTPS blocker</span><div class="track"><div class="fill" style="width:60%"></div></div><span class="pct">60%</span><span class="owner">PM+Owner</span></div>
<div class="yd-progress-summary"><span class="label">平均 · 7 项未完成</span><div class="track"><div class="fill" style="width:74%"></div></div><span class="pct">74%</span></div>
<br/>
<p><strong>产品迭代 ITER-01</strong></p>
<div class="yd-progress-row"><span class="id">ITER-01d</span><span class="name">文档 sync M1/旺财</span><div class="track"><div class="fill" style="width:85%"></div></div><span class="pct">85%</span><span class="owner">PM</span></div>
<div class="yd-progress-summary"><span class="label">平均 · 1 项未完成</span><div class="track"><div class="fill" style="width:85%"></div></div><span class="pct">85%</span></div>
<br/>
<p><strong>PM×营销全环节联合审查 6/4–6/12</strong></p>
<div class="yd-progress-row"><span class="id">PM-MKT-01</span><span class="name">全站环节审查矩阵+会议</span><div class="track"><div class="fill" style="width:15%"></div></div><span class="pct">15%</span><span class="owner">PM+营销</span></div>
<div class="yd-progress-summary"><span class="label">平均 · 1 项未完成</span><div class="track"><div class="fill" style="width:15%"></div></div><span class="pct">15%</span></div>
<br/>
<p><strong>ITER-03 开户路线+销售通知 6/4–6/18</strong></p>
<div class="yd-progress-row"><span class="id">ITER-03b</span><span class="name">抖音真实拉评 Worker</span><div class="track"><div class="fill" style="width:85%"></div></div><span class="pct">85%</span><span class="owner">后端 Lane I</span></div>
<div class="yd-progress-row"><span class="id">ITER-03c</span><span class="name">七步⑤ 5a/5b/5c 彩排</span><div class="track"><div class="fill" style="width:70%"></div></div><span class="pct">70%</span><span class="owner">QA</span></div>
<div class="yd-progress-summary"><span class="label">平均 · 2 项未完成</span><div class="track"><div class="fill" style="width:77%"></div></div><span class="pct">77%</span></div>
<br/>
</div>

## 纯文本横向（终端 / 复制）

### Sprint-R1 研发攻坚 6/3–6/16

```text
ID         任务                     进度条                                               pct  主责
ARCH-04    HTTPS + compose 实跑     ████████████████████████████████████████████████   99%  架构
QA-04      Locust 冒烟→72h          ██████████████████████████████████████████████░░   96%  QA
BJ-01      Formily site-editor    ████████████████████████████████████████████████   99%  前端
PAT-02     新颖性检索 memo             ████████████████████████████████████████████░░░░   92%  IP/专利
COMP-06    律师复审表                  █████████████████████████████████████████████░░░   93%  IP
—平均—                              ██████████████████████████████████████████████░░   95%
```

### 业务链缺口 MOD

```text
ID         任务                     进度条                                               pct  主责
MOD-01     独立域/SSL 实机             ████████████████████████████████████████████████   99%  架构
MOD-02     询盘 IM 生产密钥             ███████████████████████████████████████████████░   98%  后端
MOD-03     40 平台 PM 签字            ██████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░   45%  PM
MOD-04     七步实机录屏                 ████████████████████████████████████░░░░░░░░░░░░   75%  QA
MOD-06     出海计 App 上架包            ████████████████████████████████████████████████   99%  App
MOD-07     贸易情报矩阵签字               ██████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░   45%  PM
MOD-08     5+5 平台+HTTPS blocker   █████████████████████████████░░░░░░░░░░░░░░░░░░░   60%  PM+Owner
—平均—                              ████████████████████████████████████░░░░░░░░░░░░   74%
```

### 产品迭代 ITER-01

```text
ID         任务                     进度条                                               pct  主责
ITER-01d   文档 sync M1/旺财          █████████████████████████████████████████░░░░░░░   85%  PM
—平均—                              █████████████████████████████████████████░░░░░░░   85%
```

### PM×营销全环节联合审查 6/4–6/12

```text
ID         任务                     进度条                                               pct  主责
PM-MKT-01  全站环节审查矩阵+会议            ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   15%  PM+营销
—平均—                              ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   15%
```

### ITER-03 开户路线+销售通知 6/4–6/18

```text
ID         任务                     进度条                                               pct  主责
ITER-03b   抖音真实拉评 Worker          █████████████████████████████████████████████░░░   85%  后端 Lane I
ITER-03c   七步⑤ 5a/5b/5c 彩排        ██████████████████████████████████░░░░░░░░░░░░░░   70%  QA
—平均—                              █████████████████████████████████████░░░░░░░░░░░   77%
```

---
*pct=100 的任务不显示；S2 人类签字链见分配表*

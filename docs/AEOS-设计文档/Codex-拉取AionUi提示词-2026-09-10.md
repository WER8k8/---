# 给 Codex 的执行提示词 · 拉取 AionUi

> **用法**：把下面横线以内的**全部内容**原样复制给 Codex 执行。
> **目标**：把 AionUi 浅克隆到优丁工作区的 `_external/` 下，并按项目惯例写一份集成说明 + 一份侦察报告。

---

## 【任务】拉取 AionUi 到优丁工作区 `_external/`

### 背景
优丁项目（工作区 `C:\Users\Administrator\Documents\上线网站开发完成`）采用「外部项目参考目录」惯例：
外部开源项目统一浅克隆到 `_external/<项目名>/`，并配一份 `INTEGRATION_NOTES.md`。
现有同目录项目：`deer-flow`、`ecc`、`agency-agents-zh`、`goodjob-crm`、`trade-ai-agent`。

### 目标项目
- **名称**：AionUi
- **仓库**：`https://github.com/iOfficeAI/AionUi.git`
- **默认分支**：`main`
- **许可证**：Apache-2.0（安全，无 copyleft 约束）
- **语言**：TypeScript
- **体积**：仓库约 **679 MB**（含历史）
- **定位**：开源 24/7 Cowork 应用，统一驱动 OpenClaw / Hermes / Claude Code / Codex / OpenCode 等 **20+ CLI Agent**

> **拉取方式说明**：本次采用**全量克隆（不做 `--depth=1` 浅克隆）**。
> 原因：本项目要长期评估并可能融合 AionUi，需要完整 git 历史（看版本演进、后续可正常
> `git pull` 更新）。磁盘充足（约 268 GB 可用），全量克隆的额外成本可接受。
> 注：项目既有惯例（`ecc`、`_ref/`）用浅克隆是为了「省磁盘、够审计」，
> 本次因用途不同而改用全量。

### 执行步骤

**第 1 步：全量克隆**
```bash
cd "C:\Users\Administrator\Documents\上线网站开发完成\_external"
git clone https://github.com/iOfficeAI/AionUi.git aionui
```
> 不加 `--depth`，拉完整历史。约 679 MB，耗时可能较长；若中途失败可重试。
> 若网络受限导致全量克隆不可行，**先如实报告**，再降级为 `--depth=1` 并注明。

**第 2 步：验证克隆成功**，确认以下四点并记录实际值：
```bash
cd "C:\Users\Administrator\Documents\上线网站开发完成\_external\aionui"
git log -1 --format="%h %ad %s" --date=short     # 记下最新 commit 与日期
git rev-parse --abbrev-ref HEAD                   # 应为 main
ls                                               # 确认目录结构存在
cat package.json | head -30                      # 记下 name/version/scripts
```

**第 3 步：统计规模**（用于写说明）
- 文件总数（排除 `.git` 与 `node_modules`）
- 顶层目录清单

**第 4 步：写 `INTEGRATION_NOTES.md`**
按同目录 `ecc/INTEGRATION_NOTES.md` 的格式，在 `_external/aionui/` 下新建 `INTEGRATION_NOTES.md`，包含：
```markdown
# AionUi 集成说明（INTEGRATION_NOTES）

> **拉取时间**：<今天日期>
> **源仓库**：https://github.com/iOfficeAI/AionUi
> **许可证**：Apache-2.0（与本项目兼容）
> **拉取方式**：`git clone https://github.com/iOfficeAI/AionUi.git`（全量，含完整历史）
> **本机大小**：约 <N> 文件 / <X> MB
> **本目录位置**：`_external/aionui/`
> **commit**：<第 2 步记录的 hash 与日期>

---

## 一、AionUi 是什么
<用 3-5 句概括>

## 二、为什么引入
优丁项目需要一个「外层编排层」（需求拆解 → 内层 Hermes 调度）。当前项目的
`backend/app/services/hermes/harness_gateway.py` 是**死代码（桩）**，无人调用。
AionUi 是一个现成的、能统一驱动多 CLI Agent 的 Cowork 层，且已支持项目在用的
OpenClaw 与 Hermes，可作为外层编排的候选实现。

## 三、许可证
Apache-2.0 —— 可商用、可修改、可分发，需保留版权声明。与项目现有许可纪律兼容。

## 四、技术栈
<从 package.json 与实际目录提取>

## 五、目录结构
<顶层目录 + 一句话职责>

## 六、待办
- [ ] 侦察其 Agent 适配层实现（见下方报告）
- [ ] 评估作为外层编排接入的可行性
- [ ] 决定是否纳入 SYSTEM-LOCK-02 八大子系统的①/②层
```

**第 5 步：写侦察报告**
在 `_external/aionui/RECON.md` 中记录（**只读分析，不要运行构建、不要 `npm install`**）：
1. **它怎么接入 CLI Agent**：找到适配/驱动 CLI Agent 的代码位置（关键词：`openclaw`、`hermes`、`claude`、`codex`、`acp`、`agent`），列出文件路径
2. **通信协议**：用的是什么（ACP？stdio？HTTP？），给出关键文件
3. **能否自定义助手/组队**：对应代码在哪
4. **前后端结构**：是 Electron 应用还是 Web 应用？入口文件在哪
5. **与优丁对接的接口面**：有没有可被外部调用的 API / 事件 / 插件机制
6. **不确定的地方如实标注**，不要猜测

### 约束（重要）
- **不要修改**工作区任何既有文件；只在 `_external/aionui/` 内新增两个 md
- **不要执行** `npm install` / `pnpm install` / 构建命令（体积大、耗时长，本次不需要）
- **不要**动 `_external/` 下其他项目
- 若克隆失败或网络受限，**如实报告错误**，不要伪造结果

### 交付
执行完回报：clone 是否成功、commit hash 与日期、文件数、`INTEGRATION_NOTES.md` 与 `RECON.md` 的路径，以及第 5 步侦察的关键发现摘要。

---

*本提示词由 Claude 于 2026-09-10 生成，供 Codex 执行。*

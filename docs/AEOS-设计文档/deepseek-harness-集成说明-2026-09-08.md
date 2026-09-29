# DeepSeek Harness 接入说明（2026-09-08）

> 来源：开源仓库 [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)
> 许可：MIT｜当前版本：v0.1.3-alpha.2（developer preview，可能有破坏性变更）
> 定位：**外层编排大脑**（"一切皆插件" Agent 运行时），位于 Hermes 内层之上。

## 1. 已完成的事实动作

- ✅ vendored **最新完整源码快照**到工作区根：`deepseek-harness/`（v0.1.3-alpha.2，81MB，来自用户提供的 `C:\Users\Administrator\Documents\deepseek-harness-dsh-v0.1.3-alpha.2`，无 `.git`，为官方发布源码快照，含 `python/` SDK + `native/` + `packages/` + `apps/` + `vendor/`）。已与 Documents 原份逐字节核对一致（9340 文件数、版本号、关键路径全同）。早期的 GitHub 浅克隆 `deepseek-harness.gitclone.archive` 已删除；用户原提供的 `Documents/deepseek-harness-dsh-v0.1.3-alpha.2` 因沙箱安全策略禁止对 Dedicated 个人目录执行销毁/回收站操作而保留（与项目内副本完全相同，可手动在资源管理器删除，或留作额外备份）。
- ✅ 确认**源码不含预编译 `dsh` 运行时 exe**（已在 `native/landlock-run` 与全树校验，无 `*.exe`/`*.node`）；可运行的原生 `dsh` 由后端 venv 内 PyPI 轮子 `deepseek-harness-sdk 0.1.2rc1` + `deepseek-harness-runtime-bin`（已 `pip install` 进 backend venv）提供，`bundled_runtime_path()` 解析到位。
- ✅ 确认此前项目内仅把 DeepSeek 当作**模型供应商**（`AI_DEEPSEEK_*`），并不存在 "DeepSeek Harness" 外层运行时——现已补齐。
- ✅ 在后端新建接入包 `backend/app/services/deepseek_harness/`（config + client，SDK 懒加载）。
- ✅ 新增路由 `backend/app/api/v1/routes/deepseek_harness.py`，被自动路由发现挂载为 `/api/v1/deepseek-harness/*`。
- ✅ 在 `hermes_task_bridge.ROUTERS` 注册 `task_type="deepseek_harness"`，使统一编排入口 `/orchestration/tasks` 也能把外层请求路由到 dsh。
- ✅ 提供安装脚本 `启动脚本/setup-deepseek-harness.bat` / `.sh`。

## 2. 架构定位

```
外部请求 / 上传事件 / n8n 入站
        │
        ▼
  统一任务面 ai_tasks  ──►  Control Plane（orchestration 路由）
        │
        ├─ task_type=deepseek_harness ─► 【外层】DeepSeek Harness (dsh)  ◄── 本次接入
        │                                     │ 产物/结论
        │                                     ▼
        ├─ task_type=ai_site_build  ─► 【内层】Hermes 编排（site_build / ubrain ...）
        └─ ...                                 │
                                              ▼
                                     执行器（ECC / DeerFlow / n8n / Browser 取证）
```
dsh 通过官方 Python SDK 启动一个**打包好的原生 `dsh` 可执行文件**（子进程），经 stdio 上的
newline-delimited JSON-RPC 通信；**不依赖系统 Node.js**。

## 3. 安装（让 SDK 真正可运行）

SDK 的运行时是平台原生二进制（Windows 为 `deepseek-harness-sdk-runtime-win32-x64.exe`），
由 PyPI 上的 `deepseek-harness-runtime-bin` 轮子随 `deepseek-harness-sdk` 自动带入：

```bat
启动脚本\setup-deepseek-harness.bat
```
或
```bash
pip install deepseek-harness-sdk
```

> 若需从 vendored 源码安装（而非 PyPI 发布版），使用 `uv`：
> `uv pip install ./deepseek-harness/python/sdk`（其 `pyproject.toml` 已把 runtime 指向 `../sdk-runtime`）。
> 若要从源码构建原生二进制，需要 `pnpm`（仓库 `packageManager: pnpm@11.7.0`）+ Node ≥22.19，
> 执行 `pnpm install && pnpm run build`，再 `scripts/build-exe-for-python-sdk.ts`——通常无需，直接用 PyPI 轮子即可。

## 4. 运行 / 验证

后端路由（需登录）：
- `GET  /api/v1/deepseek-harness/health` → 返回 SDK 是否安装、二进制路径、配置、是否有 API Key。
- `POST /api/v1/deepseek-harness/invoke` → body `{ "prompt": "...", "session_id?": "...", "profile?": "sdk-minimal" }`，返回 `final_response`。

统一编排入口（推荐）：
```json
POST /api/v1/orchestration/tasks
{ "task_type": "deepseek_harness",
  "input_data": { "prompt": "把这张自行车图做成独立站的首页文案" } }
```

健康检查（无需 SDK 也能跑，验证后端装配）：
```python
from app.services.deepseek_harness.client import health, is_available
print(is_available(), health())
```

## 5. 配置项（环境变量，均可覆盖）

| 变量 | 默认 | 说明 |
|---|---|---|
| `DSH_HOME` | `<workspace>/.dsh-home` | dsh 运行时家目录（**显式**，SDK 永不读 `~/.dsh`） |
| `DEEPSEEK_HARNESS_WORKSPACE` | `<workspace>/deepseek-harness-workspace` | agent 工作区 cwd |
| `DEEPSEEK_HARNESS_PROFILE` | `sdk-minimal` | dsh profile；`sdk` 为全量插件集 |
| `DEEPSEEK_HARNESS_PROVIDER` | `deepseek-official` | provider 路由 |
| `DEEPSEEK_HARNESS_MODEL` | `deepseek-v4-flash` | 模型 id |
| `DEEPSEEK_HARNESS_REASONING_EFFORT` | 空 | 可选推理强度 |
| `DEEPSEEK_HARNESS_MAX_TOKENS` | 空 | 可选输出上限 |
| `DEEPSEEK_API_KEY` / `AI_DEEPSEEK_API_KEY` | 空 | **运行时必需**；优先复用项目 `AI_DEEPSEEK_API_KEY` |
| `DEEPSEEK_BASE_URL` / `AI_DEEPSEEK_BASE_URL` | 空 | 复用项目 `AI_DEEPSEEK_BASE_URL` |

## 6. 注意事项

1. **Developer preview**：上游 API / profile 语法可能破坏性变更，升级时留意 `SAFETY.md` 与 release notes。
2. **需要 DeepSeek API Key**：`run_turn` 在 `initialize` 阶段校验 provider/model/key，缺 Key 会失败（已统一转 502 返回清晰错误）。
3. **每次 turn 独立启停子进程**：保证并发安全、出错必回收；高频场景可后续改为连接常驻 `dsh web`（3080）HTTP 服务。
4. **懒加载**：未安装 SDK 时后端照常启动，仅 `/deepseek-harness/*` 与对应编排任务返回不可用，不会拖垮其他路由。
5. **git 隔离**：`deepseek-harness/`（vendored 源码，自带 `.git`）位于工作区根，不在后端 git 跟踪内；`.dsh-home` / `deepseek-harness-workspace` 为运行时目录，亦不入库。

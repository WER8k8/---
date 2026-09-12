# 中文片出海 — 异步任务设计（P0 + P1）

## 目标

- API **<2s** 返回 `job_id`，听写/出海在 Worker 执行
- 15+ 租户并发：**入队不丢单**，状态可轮询 / SSE 推送
- 开发无 Redis 时：**进程内线程降级**（与 `media_render_worker` 一致）
- 生产：**Celery 队列 `cross_border`**，可水平扩展 Worker
- 长视频（>6min）：**ffmpeg 分片 + 单 Worker 内 ThreadPool 并行听写 + 扇入合并**

## 状态机（复用 `media_render_tasks`）

| scenario | 含义 |
|----------|------|
| `cross_border_transcribe` | 中文听写 |
| `cross_border_dub` | 翻译 + SRT / 配音 / 烧录 |

```
queued → rendering → done | failed
         progress 0–100
```

任务 `script` 存 JSON payload；结果写入 `edit_config.cross_border_result`；进度事件写入 `edit_config.cross_border_events`（最近 40 条，API 返回末 10 条）。

## API

| 方法 | 路径 | 行为 |
|------|------|------|
| POST | `/cross-border/video-dub/transcribe` | 入队听写 → `{ job_id, status: queued }` |
| POST | `/cross-border/video-dub/jobs` | 入队出海 → `{ job_id, status: queued }` |
| GET | `/cross-border/video-dub/jobs/{job_id}` | 轮询进度与结果 |
| GET | `/cross-border/video-dub/jobs/{job_id}/events` | **SSE** `text/event-stream`，终态后结束 |

## 调度

1. `cross_border_job_service.enqueue_*` 创建 `MediaRenderTask` 并校验租户配额
2. `dispatch_cross_border_job(job_id)`：
   - Redis/Celery 可用 → `cross_border_tasks.*.delay(job_id)`
   - 否则 → 守护线程 `run_cross_border_job_background(job_id)`
3. Worker 启动时 `warm_whisper_model()` 预热 faster-whisper 单例

## 配额（P0）

- 每租户同时 `queued|rendering` 的 cross_border 任务 ≤ **2**
- 全局 `queued` 深度 > **50** → `503 QUEUE_FULL`

## P1：分片扇出扇入

| 模块 | 说明 |
|------|------|
| `audio_chunk_service.py` | `>360s` 按 5min 切段；`ThreadPoolExecutor` 最多 4 路并行 |
| `audio_asr_service.py` | 短视频整段听写；长视频走分片路径 |
| `whisper_model_pool.py` | faster-whisper 进程内单例 + 预热 |

扇入：`merge_chunk_transcripts` 合并文本与时间轴（offset 平移）。

## P1+（未做）

- 多机 Celery `group`/`chord` 分片（当前并行限于单 Worker 进程）
- 独立 GPU Worker 池

## 听写引擎优先级

**配齐讯飞三件套时默认「讯飞整段直传」**（`XFYUN_LFASR_APP_ID` + `XFYUN_LFASR_API_KEY` + `XFYUN_LFASR_SECRET_KEY`，对应控制台 APPID / APIKey / APISecret，接口 `office-api-ist-dx.iflyaisol.com`）。设 `XFYUN_LFASR_PREFERRED=0` 可改回本地优先。

| 顺序（讯飞已配） | 后端 | 配置 |
|------|------|------|
| 1 | `xfyun_ifasr_llm` | 三件套 + [Ifasr LLM 文档](https://www.xfyun.cn/doc/spark/asr_llm/Ifasr_llm.html) |
| 2 | `faster_whisper` | 本机 + ffmpeg |
| 3 | `openai_whisper` | `AI_OPENAI_API_KEY` |
| 4 | `gemini_audio` | `AI_GEMINI_API_KEY` |

旧版 raasr（`raasr.xfyun.cn`）：`XFYUN_LFASR_BASE_URL=https://raasr.xfyun.cn/api` 且留空 `XFYUN_LFASR_API_KEY`，backend 为 `xfyun_lfasr`。

## 生产 Worker

```bash
celery -A app.tasks.celery_app worker -Q cross_border -c 4
```

## 前端

- `pollCrossBorderJob` 优先 SSE（`Authorization` + fetch 流），失败降级 2s 轮询
- `video-overseas.vue` 展示 `progress` / `hint`
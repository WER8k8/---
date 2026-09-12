# 中文片出海 · 全媒体工作室集成宪章

> **产品 ID**：`CROSS-BORDER-MEDIA-STUDIO-01`  
> **机器契约**：`.project/cross-border-media-studio.json`  
> **PM 蜂群**：Sprint-R2 新增泳道 MS-A～MS-F（与 R1 并行，不阻塞 cert:gate）

---

## 一、产品愿景（全都要，但不假交付）

租户一条链路完成：**上传中文片 → 自动听写/翻译/配音 → 多轨剪辑校对 → 分发**，底层「全都要」：

| 能力层 | 已集成 | 排期中 | 评估 |
|--------|--------|--------|------|
| **听写 ASR** | 讯飞大模型、LFASR、本机 Whisper、OpenAI、Gemini 兜底 | 浏览器 Whisper | — |
| **翻译/脚本** | LLM `invoke_llm` | — | — |
| **配音 TTS** | edge-tts + ffmpeg | 云端 TTS | — |
| **剪辑 UI** | 优丁预览 + 剪辑台枢纽 | Fly-Cut、OpenCut、Twick | OpenReel |

**硬门禁**：未配置引擎不得报 `configured: true`；无 Worker/无密钥不得假成功（见 `01-no-fake-delivery-hardgate.mdc`）。

---

## 二、用户动线

```text
/client/video-overseas     选视频 → 一键出海（auto_asr job）
        │
        ▼
/client/video-studio       能力探测 + 引擎状态 + 进阶剪辑入口
        │
        ├── Fly-Cut（Vue3 iframe PoC）     MS-FE-03
        ├── OpenCut（React 子应用 PoC）   MS-FE-04
        └── 下载 SRT / 成品 → 外链剪映（过渡）
        │
        ▼
/client/distribute         内容分发
```

---

## 三、蜂群泳道（专家并行）

| Lane | 任务 ID | 主责 | In-Scope | Out-of-Scope |
|------|---------|------|----------|--------------|
| **MS-A** | MS-ARCH-01 | 架构 | `media_studio_capability_registry`、契约 JSON、GET `/media-studio/capabilities` | 不改 Formily / 全局路由 |
| **MS-B** | MS-FE-01/02 | 前端 | `video-studio.vue` 枢纽、`video-overseas` 跳转 | fork 编辑器进 `admin/src` |
| **MS-C** | MS-FE-03 | 前端 | Fly-Cut `_ref/` + iframe 握手 | OpenCut 代码 |
| **MS-D** | MS-FE-04 | 前端 | OpenCut 独立子应用 / 微前端 | Vue 主包 React 混写 |
| **MS-E** | MS-BE-01 | 后端 | studio project CRUD（SRT/segments JSON） | 新 ASR 厂商（除非 PM 开单） |
| **MS-F** | MS-QA-01 | QA | E2E 出海→剪辑台→分发；honesty 扫描 | 修功能逻辑（开单 Lane 主责） |

---

## 四、编辑器选型（对照仓 `_ref/`）

| 项目 | 栈 | 集成方式 | 优先级 |
|------|-----|----------|--------|
| [Fly-Cut](https://github.com/x007xyz/fly-cut) | Vue3 | iframe + postMessage 传 `editor_handoff` | **P0** |
| [OpenCut](https://github.com/OpenCut-app/OpenCut) | React | 子域或 `/studio-opencut/` 独立部署 | P1 |
| [Twick](https://github.com/ncounterspecialist/twick) | React SDK | 嵌入 React 壳 | P2 |
| OpenReel / FreeCut | React | 仅评估，不做首版 | P3 |

**隔离规则**：对照源码放 `_ref/<name>/`，**禁止**提交进 `frontend/admin/src` 核心树。

---

## 五、接口契约（handoff）

一键出海 job 完成后，剪辑台接收：

```json
{
  "media_task_id": "uuid",
  "video_url": "/uploads/....mp4",
  "srt_url": "/uploads/....srt",
  "transcript_zh": "...",
  "script_en": "...",
  "segments": [],
  "asr_backend": "xfyun_ifasr_llm"
}
```

**已实现**：`GET /api/v1/cross-border/media-studio/capabilities`  
**MS-BE-01 已落地**：`GET/POST /api/v1/cross-border/media-studio/projects/{media_task_id}`

---

## 六、阶段交付

| 阶段 | 交付 | 验收 |
|------|------|------|
| **R2-0（当前）** | 能力注册表 + 剪辑台枢纽页 + 出海页跳转 | API 200；`configured` 与 env 一致 |
| **R2-1** | Fly-Cut iframe PoC，导入 SRT + 原片 | 手测改字导出 SRT |
| **R2-2** | studio project 持久化 + 回写 job | 刷新不丢字幕稿 |
| **R2-3** | OpenCut 子应用 + 端侧 Whisper 可选 | 短视浏览器听写降本 |
| **R2-4** | QA E2E + 站会 `needs_owner` 清零 | `e2e_cross_border` + honesty P0=0 |

---

## 八、Vozo AI（评估中 · 高匹配度）

[Vozo](https://www.vozo.ai/) 是 **「视频翻译 + AI 配音 + 口型同步 + 画面字翻译」** 一体化 SaaS，与租户目标「中文带货片 → 英文可发版」高度重合。

| 能力 | 我们自研链 | Vozo |
|------|-----------|------|
| 中文听写 | 讯飞/Whisper ✓ | 内置 ASR ✓ |
| 英译 + 字幕 | LLM + SRT ✓ | Translate API ✓ |
| 英文配音 | edge-tts（机械感） | VoiceREAL 克隆 ✓ |
| **口型同步** | ✗ | LipREAL ✓ |
| **画面中文改英文** | ✗ | Visual Translate ✓ |
| 术语表 | `glossary_helper` ✓ | glossary_ids ✓ |
| 数据留在自有服务器 | ✓ | 视频需上传 Vozo |
| API | 已有 job 链 | [Enterprise API](https://www.vozo.ai/docs/api_reference/get_started)（联系 bd@vozo.ai） |

**建议定位（双轨，不互斥）**

| 模式 | 场景 | 输出 backend |
|------|------|--------------|
| **标准轨** | 成本敏感、数据不出域、可接受 edge-tts | `self_hosted` |
| **精品轨** | 口播带货、要口型/克隆声/画面字 | `vozo_ai`（MS-G 泳道） |

**MS-G 接入要点（待 Enterprise Key）**

1. `POST` Translate & Dub：`media_url` + `zh-CN` → `en-US` + 可选 `glossary_ids`
2. Webhook 或轮询 task_id → 落库 `cross_border_result`（禁止无 Key 假成功）
3. 前端出海页增加「精品出海（Vozo 口型版）」— 仅 `VOZO_API_KEY` 配置后可见
4. 与 Fly-Cut/OpenCut：**Vozo 出成片 → 剪辑台微调** 再分发

**环境变量（预留）**：`VOZO_API_KEY`、`VOZO_WEBHOOK_SECRET`

---

## 九、开源对标（Vozo / 山海智影 · MS-H）

**山海智影**（媲美科技）是商业短剧译制平台，**未见公开 GitHub 开源仓**；能力上最接近的开源组合如下。

### 能力对照

| 能力 | Vozo | 山海智影（商业） | 我们自研 | 开源可集成 |
|------|------|------------------|----------|------------|
| 中文听写 | ✓ | ✓ | 讯飞/Whisper ✓ | KrillinAI / pyVideoTrans |
| 英译+字幕 | ✓ | ✓ | LLM ✓ | 同上 |
| 克隆配音 | VoiceREAL ✓ | ✓ | edge-tts（弱） | Linly / v2vt / pyVideoTrans |
| **口型同步** | LipREAL ✓ | ✓ | ✗ | **Linly-Dubbing**、**v2vt**、MuseTalk 组件 |
| **硬字幕擦除** | Visual Translate 部分 | ✓ | ✗ | **NarratorAI** |
| **画面字翻译** | Visual Translate ✓ | 部分 | ✗ | 暂无成熟开源（商业 Vozo 独擅） |
| 数据不出域 | ✗（上传云端） | 视部署 | ✓ | 开源自托管 ✓ |

### 三轨产品策略（全都要）

| 轨道 | 场景 | Provider ID |
|------|------|-------------|
| **标准轨** | 成本敏感、现有 job 链够用 | `self_hosted`（已集成） |
| **开源精品轨** | 要口型/克隆、视频留在自有 GPU | `linly_dubbing` / `v2vt` / `krillinai`（MS-H） |
| **商业精品轨** | 要画面字+口型、接受 SaaS | `vozo_ai`（MS-G） |

### 推荐集成顺序（MS-H）

1. **KrillinAI CLI** — 与现有 Python job 链最顺：`KRILLINAI_CLI_PATH` 子进程跑 `pipeline`，回写 SRT/成片 URL。
2. **Linly-Dubbing sidecar** — 口播带货首选开源对标山海智影：`LINLY_DUBBING_BASE_URL` HTTP 封装。
3. **v2vt** — 中英互译+口型一体：`V2VT_SERVICE_URL`。
4. **MuseTalk** — 仅口型后段：自研链 TTS 完成后调用 `MUSETALK_SERVICE_URL`。
5. **NarratorAI** — 短剧硬字幕擦除+译制：`NARRATOR_AI_BASE_URL`。

注册表：`opensource_localization_registry.py` · 能力 API 已聚合；**未配置 sidecar/CLI 时 `configured=false`，禁止假出片**。

**环境变量**：`KRILLINAI_*`、`LINLY_DUBBING_BASE_URL`、`YOUDUB_WEBUI_BASE_URL`、`VIDEOLINGO_BASE_URL`、`V2VT_SERVICE_URL`、`NARRATOR_AI_BASE_URL`、`PYVIDEOTRANS_*`、`MUSETALK_SERVICE_URL`、`OPENSOURCE_LOCALIZATION_PREFERRED`（留空则智能选型）。

### 智能最优栈（已写入契约 `recommended_stack`）

| 场景 | 选型 | 理由 |
|------|------|------|
| **默认日常** | `self_hosted` | 已上线、讯飞已配、成本最低 |
| **开源口型精品** | **Linly-Dubbing** | 最接近山海智影/Vozo 口型，CosyVoice 克隆 |
| **开源集成首选** | **YouDub-webui** | B站中文→英文成熟、FastAPI 易接 sidecar |
| **字幕精品** | VideoLingo | 术语+Netflix 级字幕 |
| **短剧擦字幕** | NarratorAI | 硬字幕无痕擦除 |
| **商业顶配** | Vozo | 画面字+口型（有 Key 再开） |

自动优先级：`linly_dubbing` → `youdub_webui` → `v2vt` → `krillinai` → …（见 `OPTIMAL_PICK_ORDER`）

---

## 十、MS-H/MS-BE 已落地（精品轨 + 剪辑台持久化）

| 能力 | 路径 |
|------|------|
| 精品 job | `POST /cross-border/video-dub/premium-jobs` · `kind=premium` |
| 开源执行器 | `opensource_localization_service.py` · sidecar 契约 `.project/opensource-sidecar-contract.json` |
| Vozo 骨架 | `vozo_localization_service.py`（有 Key 才调 API，无输出则失败） |
| Studio 持久化 | `GET/POST /cross-border/media-studio/projects/{media_task_id}` |
| 参考 sidecar | `scripts/youding-sidecar-reference.py`（开发探针用，不产出真 mp4） |
| 前端 | 出海页「精品出海」按钮 · 剪辑台「智能推荐栈」· 项目面板 · Fly-Cut/OpenCut PoC 路由 |

**dev 真实 sidecar**：`python scripts/youding-sidecar-real.py --port 9901` + `YOUDUB_WEBUI_BASE_URL=http://127.0.0.1:9901`（健康探测 `mode=production`）。  
**禁止**：`youding-sidecar-reference.py` 为 mock，backend 不会计为已配置。  
**默认可用**：未配 GPU sidecar 时自动激活 `youding_self_hosted` 内置真实链（听写→英译→配音，无口型）。

---

## 十一、四行摘要（本批次 MS-ARCH-01 + MS-FE-01/02）

1. **目标**：全媒体工作室编排契约 + 能力探测 API + 租户剪辑台枢纽。  
2. **做法**：注册表聚合 ASR/编辑器/TTS；新路由 `/client/video-studio`；出海页「进阶剪辑台」。  
3. **验收**：`pytest test_media_studio_capability_registry.py`；Admin 打开剪辑台见引擎列表。  
4. **不测**：Fly-Cut/OpenCut 本体集成（MS-FE-03/04 后续泳道）。

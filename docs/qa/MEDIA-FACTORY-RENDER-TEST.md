# 多媒体工厂 · 视频生成效果检验记录

> **最后跑通**：2026-06-09  
> **脚本**：`scripts/verify-media-factory-render-effect.py`  
> **机器可读**：[`media-factory-render-test-latest.json`](./media-factory-render-test-latest.json)

---

## 结论（给 PM / 老板）

| 项目 | 状态 |
|------|------|
| **链路**（建任务→渲染→下载 mp4） | ✅ 已通过 |
| **真实 AI 文生视频效果** | ❌ **尚未检验** |
| **原因** | 开发环境 `MEDIA_FACTORY_MOCK_RENDER=true`，且 `AI_NVIDIA_COSMOS_BASE_URL` 未配置 |

当前产出的是 **ffmpeg 占位短片**（约 6KB 色块），**不能**代表 Cosmos/NVIDIA 真实画面质量。

---

## 本次检验证据

- 任务 ID：`ab719eaf-2f66-44f6-861f-2dd4d4c80bff`（以 latest.json 为准）
- 结果 URL：`/uploads/media_factory/{task_id}.mp4`
- Admin 入口：`/media-factory/dashboard` · `/admin/ai-center/article-to-video`

---

## 要测「真实生成效果」需满足

1. 部署或指向 **Cosmos NIM**（`/v1/infer`），在 `backend/config/dev/.env` 填：
   ```env
   AI_NVIDIA_COSMOS_BASE_URL=http://127.0.0.1:8000   # 或云端 NIM 地址
   MEDIA_FACTORY_MOCK_RENDER=false
   ```
2. 保留 `AI_NVIDIA_API_KEY`（NIM 鉴权）
3. 重启 API，再跑：
   ```powershell
   python scripts/verify-media-factory-render-effect.py
   ```
4. 人工打开 mp4，按 **建材脚本** 验收：画面是否可读、有无乱码、时长是否 ≥2s、是否像产品展示而非纯色块

---

## PM 派工（视频 Lane GW-S）

| ID | 事项 | 验收 |
|----|------|------|
| MF-T1 | 本地/Staging 关 MOCK，跑 1 条真实 Cosmos | latest.json `verdict=real_render_ok` |
| MF-T2 | 文章→脚本→视频 全页人工走一遍 | 截图 + mp4 路径 |
| MF-T3 | UI 标明「mock / 真实渲染」 | overview.mock_render 与页面黄条一致 |

---

*QA · honest：mock 通过 ≠ 效果验收通过*

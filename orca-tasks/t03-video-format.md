## 任务：§2 视频平台格式自适应转码

工作目录：$BASE/backend
现有代码：
- backend/app/services/media_video_edit_service.py (ffmpeg clip 基础)
- backend/app/services/video_publish_orchestrator.py (发布编排)
产出：outputs/ante/t03-video-format/

### 实现：platform_video_adapter.py
路径：backend/app/services/platform_video_adapter.py

功能：
1. 定义平台规格常量：
   - TikTok: max_duration=600s, max_size=288MB, preferred_ratio=9:16, codec=h264
   - Instagram Reels: max_duration=90s, max_size=4GB, ratio=9:16 or 1:1
   - YouTube Shorts: max_duration=60s, max_size=10GB, ratio=9:16
   - YouTube Long: max_duration无限制, max_size=256GB, ratio=16:9

2. auto_adapt(video_path, target_platform) → new_path
   - 检测源视频时长/分辨率/大小
   - 超限时自动裁剪或转码
   - 复用现有 apply_video_clip / build_edit_payload

3. 集成到 publish_workers/tier_router.py 的平台选择逻辑

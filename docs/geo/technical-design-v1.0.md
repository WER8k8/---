# SourceChain-Dominance GEO Engine 移动端专用开发文档 v1.0

项目路径：`C:\Users\97907\Desktop\Cursor 888\sourcechain-geo-engine`

## 核心定位

本项目为移动端专用 GEO 询盘引擎，源码与开发文档统一放置在 `Cursor 888` 目录下。上线时与电脑端站点融合，但移动端技术能力、加载速度、设计逻辑、GEO 可见性和询盘转化保持 P0 优先级。

## 上线原则

- 移动端 H5/SSR 是 v1.0 主战场。
- 电脑端融合采用统一 API、统一产品库、统一内容库。
- 移动端保持独立性能预算、独立 UI 验收、独立 RankGuard 监测。
- 移动端 `LCP` 目标小于等于 `2.0s`，上线红线小于等于 `2.5s`。
- 移动端 `INP` 必须小于等于 `200ms`。
- 首屏必须优先展示产品名称、价格、核心参数、供货能力和拨号入口。

## GEO 目标

- 持续对标全国前十竞品。
- 每日专项监测“智推时代”等重点对手。
- 对比维度包括关键词覆盖、AI 引用、结构化数据、页面速度、首屏信息密度和移动端询盘路径。
- 排名目标作为运营 KPI 和优化方向，系统必须做到下降可检测、原因可追踪、版本可回滚、内容可补强。

## 每日 08:00 技术自进化

每天 08:00 运行 `TechRadarAgent`：

- 采集官方文档、changelog、RFC、论文摘要、开源 release、技术论坛公开内容。
- 只允许使用公开、合规、许可证兼容的技术资料。
- 不绕过登录、付费墙、验证码、robots 或访问限制。
- 不把未经测试的代码直接热更新到生产环境。

自进化发布流程：

1. 技术雷达生成候选清单。
2. 许可证与来源检查。
3. 生成补丁草案。
4. 隔离环境测试。
5. Lighthouse 移动端性能测试。
6. RAG 与结构化数据回归测试。
7. RankGuard 检查排名风险。
8. 灰度发布。
9. 指标下降自动回滚。

## 热更新和回滚

允许热更新：

- 配置项。
- 文案。
- FAQ。
- JSON-LD 内容。
- 缓存策略。
- 低风险非关键组件。

必须完整发布流程：

- Nuxt 渲染链路。
- FastAPI API schema。
- 数据库迁移。
- 核心依赖升级。
- 首页和产品页首屏结构。
- 影响排名和抓取的页面结构。

回滚条件：

- 移动端 `LCP > 2.5s`。
- `INP > 200ms`。
- API 错误率超过阈值。
- 询盘率明显下降。
- GEO 排名信号或 AI 引用信号明显下降。

## 当前源码模块

```text
backend/
  app/main.py                  FastAPI 入口
  app/agents/scheduler.py      每日 08:00 技术雷达与 RankGuard 调度骨架
  app/services/rank_guard.py   排名保护与回滚判定
  app/db/schema.sql            PostgreSQL + pgvector 数据库 schema

frontend/
  app.vue                      全局移动端样式
  pages/product/[slug].vue     移动端产品询盘页
  server/api/generate.post.ts  Nuxt 服务端生成代理
  server/utils/redis.ts        Redis 单例

infra/
  docker-compose.yml           本地部署编排
  .env.example                 环境变量模板
```

## 本地启动

```bash
cd "C:\Users\97907\Desktop\Cursor 888\sourcechain-geo-engine\infra"
docker-compose --env-file .env.example up --build
```

当前本机环境说明：

- 已检测到可用命令为 `docker-compose`，不是新版 `docker compose` 插件。
- `docker-compose --env-file .env.example config` 已校验通过。
- 若启动时报 Docker daemon 未运行，需要先打开 Docker Desktop，再执行上面的启动命令。

访问：

- 一键联调：`infra/start-dev-all.ps1`
- 后端健康检查：`http://127.0.0.1:8000/health`
- 移动端产品页：`http://127.0.0.1:3000/product/polyurethane-lightweight-concrete`
- 询盘接口（经 Nuxt 代理）：`POST http://127.0.0.1:3000/api/leads`

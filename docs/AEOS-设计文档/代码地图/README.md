# 代码地图 · 索引

> 由 `tools/code_atlas_gen.py` + `tools/code_atlas_md.py` 从源码生成，**可随时重跑校验**。机读全量见 `atlas.json`。
> 每行一个文件：`路径`（行数）— 摘要 · 关键符号 · ⚑标记。
> ⚑ 标记含义：MOCK=含 mock/simulate/假数据字样；STUB=TODO/占位；DEGRADED=降级/兜底；DEPRECATED=弃用。
> **注意**：⚑ 是关键词命中，不是判定；是否真为桩需人读确认。

- [后端主应用 backend/app](backend-app.md) — 1163 个文件 · 后端主应用（api/models/services/core/tasks…）
- [后端测试 backend/tests](backend-tests.md) — 58 个文件 · 后端测试
- [后端脚本 backend/scripts](backend-scripts.md) — 46 个文件 · 后端脚本（含 orchestration_selfcheck.py）
- [超管后台 frontend/admin/src](frontend-admin.md) — 561 个文件 · 超管/多角色后台（Vite+Vue3+AntD）
- [官网/租户站 frontend（Nuxt3 开发版）](frontend-web.md) — 254 个文件 · 官网/租户站（Nuxt3 开发版）
- [SEO 矩阵后台 seo-admin/src](seo-admin.md) — 29 个文件 · SEO 矩阵后台（Vite+Vue3+ElementPlus）
- [SEO 矩阵后端 seo-backend/src](seo-backend.md) — 73 个文件 · SEO 矩阵后端（Node/Express）
- [Cloudflare Workers](workers.md) — 5 个文件 · Cloudflare Workers（爬取/提取/传输）
- [技能包 skills/](skills.md) — 254 个文件 · 76 个业务技能 SKILL.md
- [3000 官网运行源 主要备份/上线网站/frontend](runtime-source.md) — 296 个文件 · 3000 官网运行源（Vite 暖白+砖橙）
- [运行源内嵌 admin 子应用（重复副本）](runtime-admin.md) — 1783 个文件 · 运行源内嵌的独立 admin 子应用（重复副本）

**合计 4522 个文件**（不含 node_modules/.git/构建产物/第三方）。
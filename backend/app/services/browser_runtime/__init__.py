"""Browser Runtime（P5）— Playwright + CDP 浏览器执行层（总纲 §4.7）。

本轮 25-B 仅落地骨架（runtime 核心 + 租户 Profile 隔离 + 证据回传 + Policy 闸门），
不做真实浏览器调用实现。下一迭代 25-C 起逐步接入具体执行场景
（合规发布、自动化数据采集、UI 验证等）。所有路径默认关 + 懒导入：

- 开关 `BROWSER_RUNTIME_ENABLED` 默认 False：禁用时所有调用降级 noop；
- 白名单 `BROWSER_RUNTIME_ALLOWED_TENANTS` 默认空：开启后只对白名单租户开放；
- Playwright 依赖运行时检测：未安装则降级 noop 并 warning，**绝不抛错**；
- 任何异常吞掉 + 证据化记录，调用方主链路（DeerFlow/UBrain/Hermes）不受影响。

红线（与既有体系一致）：
- R5 永不引入 GoodJob whatsapp-plugin（GPL-3.0）—— Playwright 是 Apache-2.0，OK；
- R9 访客输入不可信—— 任何 browser 输入/输出必经 brand_guard 净化（不在本轮）；
- 每租户独立 Profile（cookies/storage/缓存物理隔离）—— 防跨租户泄漏。
"""

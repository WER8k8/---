# Agent KPI 白底色条 · 组件规范（UX-02）

> **对齐代码**：`frontend/admin/src/views/agent/performance.vue` · `commission.vue`  
> **状态**：✅ 代码已落地 · 本稿供视觉签字

## 结构

```
┌─ 左 3px brand 条 ─┬──────────────────────────────┐
│                   │  标题 15px semibold           │
│                   │  数值 24px tabular            │
│                   │  副文案 12px muted            │
└───────────────────┴──────────────────────────────┘
```

## Token

| 属性 | 值 |
|------|-----|
| 背景 | `#ffffff` · `--uj-kpi-bg` |
| 边框 | `1px #e5e7eb` |
| 左条 | `3px solid #2563eb` |
| 阴影 | `0 1px 2px rgb(15 23 42 / 4%)` |
| 圆角 | `12px` |

## 禁止

- 全卡 `linear-gradient`
- emoji 图标
- 「查看全平台」链接

*UX-02 v1 · 2026-06-02*

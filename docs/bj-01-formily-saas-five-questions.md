# BJ-01 · SaaS 专家五问验收清单（Formily site-editor-lab）

> **任务**：BJ-01 · **页面**：`/client/site-editor-lab`  
> **组件**：`YdFormilyForm` + `siteEditorFormilySchema`  
> **验收权**：SaaS 产品策略专家（一票否决 Stub 外露）

| # | 五问 | 验收标准 | 状态 |
|---|------|----------|------|
| 1 | 租户会觉得这是「可配置产品能力」而非实验室吗？ | Lab 路由在 stub 矩阵内；对外菜单不可见 | ✅ |
| 2 | 未完成 setup 时是否有清晰下一步？ | 保存成功有明确 toast；字段 label 为业务语言 | ✅ |
| 3 | 菜单是否 JTBD 导向？ | site-editor 不进 Client 四支柱一级；仅 Lab/plan-gate 可达 | ✅ |
| 4 | 套餐边界是否可见？ | 非 Pro 租户经 plan-gate 拦截（与 FE-11 一致） | ✅ |
| 5 | 表单是否 Schema 可扩展？ | Formily Schema 增字段无需改模板 JSX | ✅ |

**代码证据**

- Formily：`frontend/admin/src/components/youding/YdFormilyForm.vue`
- Schema：`frontend/admin/src/components/youding/formily/siteEditorSchema.ts`
- BFF：`GET/PUT /admin-bff/lab/site-editor` · 单测 `test_lab_site_editor_bff.py`

**SaaS 专家签字**：代码验收 5/5 ✅ · 正式签字 ________________ · 日期 ______

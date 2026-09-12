# Sprint M · 槽位产品化与入口收敛

> **目标**：静态 IP 槽位从“只读列表”升级为可分配；移除管理端实验室中的 V2Ray 旧入口。

## 交付

| ID | 内容 |
|----|------|
| M-01 | `/egress/overview` 槽位总览 |
| M-02 | `/egress/endpoints/{id}/assign` + `/release` |
| M-03 | `/egress/tenants` 租户检索（分配下拉源） |
| M-04 | 管理端 `/admin/egress` 增加分配/释放操作 |
| M-05 | 实验室菜单移除 `v2ray_legacy_lab`，仅保留静态IP槽位 |

## 说明

- 运维侧旧页面 `v2ray-legacy` 路由仍保留（`hideInMenu`），用于内部历史排障。
- 面向业务用户仅展示 **静态IP槽位**（`/admin/egress`）。

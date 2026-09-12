# `_ref/` — 开源参考仓本地镜像

> **用途**：Phase 0 深读审计 — **只读参考，不直接当生产代码**。  
> **更新**：`python scripts/clone-open-source-refs.py`  
> **清单**：`clone-manifest.json`

## 原则

1. 全部 **shallow clone**（`--depth 1`），省磁盘、够审计。  
2. 深读产出写入 `docs/open-source-audit/NN-*.md`。  
3. 抽取代码进 `frontend/youding-admin-kit` 或 `admin-vben`，**不**在 `_ref` 里改。  
4. Wave 1 编码前须完成 `99-synthesis-for-uac.md`。

## 仓库列表

见 `scripts/clone-open-source-refs.py` 内 `REPOS` 数组。

## 磁盘提示

| 库 | 约计 |
|----|------|
| vue-vben-admin | 大（monorepo） |
| vue-element-admin | 大 |
| ruoyi-plus-soybean | 大（含 Java） |
| 其余 Admin 模板 | 中 |
| daisyui / formily-antdv-x3 | 小 |

建议预留 **5–15 GB** 用于全部 `_ref`。

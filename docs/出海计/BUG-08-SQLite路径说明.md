# BUG-08：SQLite 开发库路径

## 现象

仓库**根目录**可能存在 **0 字节**的 `youding_dev.db`（误建空文件），而真正数据在 **`backend/youding_dev.db`**（约 2MB+）。  
若 `DATABASE_URL=sqlite:///./youding_dev.db` 且工作目录在根目录，预检会出现 `no such table: platforms`。

## 修复（代码）

`backend/app/core/sqlite_paths.py`：在多个候选路径中选**体积最大且非空**的库文件。

已接入：`Settings.__init__`、`rebind_engine`、`ensure_dev_sqlite.py`、`seed_platforms_full.py`、`run_production_preflight.py`。

## 建议

- 开发时删除或不要提交根目录空 `youding_dev.db`；或设置 `YOUDING_SQLITE_PATH=backend/youding_dev.db`  
- 换机备份请用 **`backend/youding_dev.db`**（`scripts/run-round2-ops.ps1` 已按非空文件备份）

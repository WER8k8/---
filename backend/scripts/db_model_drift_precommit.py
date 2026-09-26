# -*- coding: utf-8 -*-
"""pre-commit 软门禁包装：让「ORM 模型 ↔ 物理库 漂移自检」在每次本地提交时可见，
但**绝不阻断提交**。

为什么需要包装
--------------
`check_db_model_drift.py` 在模块顶层就 `import app.models` + `inspect(engine)`
直接连库，且**没有**命令行参数（不会 `--warn-only` 那种降级）。它在以下情况会
返回非 0：
  1. 本地未装后端依赖（fastapi/sqlalchemy 等）—— ImportError；
  2. 本地 PG@5433 未启动或连不上 —— OperationalError/连接超时；
  3. 改了 models/ 但模型本身导入失败（语法/循环依赖）—— 同样非 0。

第 1/2 类属于「环境不具备」或「需要活 DB」，不该阻断只改前端/文档的提交。
第 3 类虽然值得开发者注意，但若在没活 DB 的机器上也会误判，故同样只提示。
本包装统一吞掉非 0 退出码（含超时），确保本地提交永远不被自检本身卡住。

真正的硬门禁在 CI：该脚本需活 DB，CI 默认无活库，故当前**只做本地软门禁**
（如需在 CI 加硬门禁，须先有可用的 PG 服务再仿 `ci.yml` 的 router-drift 作业）。

用法（由 .pre-commit-config.yaml 的 local hook 调用，无需手动执行）：
  python backend/scripts/db_model_drift_precommit.py
"""
from __future__ import annotations

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TARGET = os.path.join(_HERE, "check_db_model_drift.py")
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

_TIMEOUT = 120  # 秒；连库可能慢/卡，超时不阻断


def main() -> int:
    if not os.path.isfile(_TARGET):
        print("[drift-gate] 未找到 check_db_model_drift.py，跳过")
        return 0
    cmd = [sys.executable, _TARGET]
    try:
        proc = subprocess.run(cmd, cwd=_BACKEND_ROOT, timeout=_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(
            "[drift-gate] ORM↔物理库漂移自检超时（>%ds，可能在等 DB 连接）。\n"
            "        如改动涉及 backend/app/models 或 alembic 迁移，请在具备后端+活 DB 环境时重跑：\n"
            "          python backend/scripts/check_db_model_drift.py\n"
            "        仅作提示，不阻断本次提交。" % _TIMEOUT
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        print(
            f"[drift-gate] 无法运行 ORM↔物理库漂移自检（{type(exc).__name__}: {exc}），"
            "仅提示，不阻断提交"
        )
        return 0
    if proc.returncode not in (0, None):
        print(
            "[drift-gate] ORM↔物理库漂移自检未完整执行（本地可能缺后端依赖或 PG@5433 未启动）。\n"
            "        如改动涉及 backend/app/models 或 alembic 迁移，请在具备后端+活 DB 环境时重跑：\n"
            "          python backend/scripts/check_db_model_drift.py\n"
            "        仅作提示，不阻断本次提交。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

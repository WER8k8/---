# -*- coding: utf-8 -*-
"""pre-commit 软门禁包装：让「路由注册漂移自检」在每次本地提交时可见，
但**绝不阻断提交**。

为什么需要包装
--------------
`check_router_registration_drift.py` 在以下情况会返回非 0：
  1. 发现真漂移（D1/D3）—— 这正是我们想让开发者「看见」的；
  2. 环境缺后端依赖且本地无 :8001 服务时，脚本回退 --live 失败会 SystemExit(1)。

第 2 类属于「环境不具备」，不该阻断只改前端/文档的提交。本包装统一吞掉非 0
退出码，确保本地提交永远不被漂移自检本身卡住。真正的硬门禁在 CI
（见 .github/workflows/ci.yml 的 router-drift 作业，直接用原脚本、无 --warn-only）。

用法（由 .pre-commit-config.yaml 的 local hook 调用，无需手动执行）：
  python backend/scripts/router_drift_precommit.py
"""
from __future__ import annotations

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TARGET = os.path.join(_HERE, "check_router_registration_drift.py")
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, ".."))


def main() -> int:
    if not os.path.isfile(_TARGET):
        print("[drift-gate] 未找到 check_router_registration_drift.py，跳过")
        return 0
    cmd = [sys.executable, _TARGET, "--warn-only"]
    try:
        proc = subprocess.run(cmd, cwd=_BACKEND_ROOT)
    except Exception as exc:  # noqa: BLE001
        print(f"[drift-gate] 无法运行路由漂移自检（{type(exc).__name__}: {exc}），仅提示，不阻断提交")
        return 0
    if proc.returncode not in (0, None):
        print(
            "[drift-gate] 路由漂移自检未完整执行（本地可能缺后端依赖或 :8001 未启动）。\n"
            "        如改动涉及 backend/app/api，请在具备后端环境时重跑：\n"
            f"          python {os.path.relpath(_TARGET, _BACKEND_ROOT)} --warn-only\n"
            "        仅作提示，不阻断本次提交。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""pre-commit 软门禁包装：让「编排链路自检(orchestration_selfcheck)」在每次本地提交时可见，
但**绝不阻断提交**。

为什么需要包装
--------------
`orchestration_selfcheck.py` 是 19 项编排门禁，退出码 0=全通 / 1=有环节未通。
它的每个检查项内部都 try/except，所以**缺活服务（PG/Celery/n8n）时不会崩，
而是把对应项 record(False) 后继续，最终 passed<total → 返回 1**。

第 1 类（环境不具备 / 需活服务）不该阻断只改前端/文档的提交；第 2 类（真有环节
未通）虽值得开发者注意，但若在没活服务的机器上也会误判为 1，故同样只提示。
本包装统一吞掉非 0 退出码（含超时），确保本地提交永远不被自检本身卡住。

真正的硬门禁在 CI：该脚本需活 PG/Celery/n8n，CI 默认无活服务，故当前
**只做本地软门禁**（未进 CI）；硬门禁若要在 CI 加，须先有可用服务再仿 `router-drift` 作业。

用法（由 .pre-commit-config.yaml 的 local hook 调用，无需手动执行）：
  python backend/scripts/orchestration_selfcheck_precommit.py
"""
from __future__ import annotations

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TARGET = os.path.join(_HERE, "orchestration_selfcheck.py")
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

_TIMEOUT = 180  # 秒；会连活服务/读外部目录，给足余量


def main() -> int:
    if not os.path.isfile(_TARGET):
        print("[drift-gate] 未找到 orchestration_selfcheck.py，跳过")
        return 0
    cmd = [sys.executable, _TARGET]
    try:
        proc = subprocess.run(cmd, cwd=_BACKEND_ROOT, timeout=_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(
            "[drift-gate] 编排链路自检超时（>%ds，可能在等活服务）。\n"
            "        如改动涉及后端编排链路，请在具备活 PG/Celery/n8n 环境时重跑：\n"
            "          python backend/scripts/orchestration_selfcheck.py\n"
            "        仅作提示，不阻断本次提交。" % _TIMEOUT
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        print(
            f"[drift-gate] 无法运行编排链路自检（{type(exc).__name__}: {exc}），"
            "仅提示，不阻断提交"
        )
        return 0
    if proc.returncode not in (0, None):
        print(
            "[drift-gate] 编排链路自检未完整通过（本地可能缺后端依赖或活服务 PG/Celery/n8n 未起）。\n"
            "        如改动涉及后端编排链路，请在具备活服务环境时重跑：\n"
            "          python backend/scripts/orchestration_selfcheck.py\n"
            "        仅作提示，不阻断本次提交。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

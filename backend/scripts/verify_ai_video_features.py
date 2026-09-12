"""功能齐全性检验（需 backend :8001 + dev .env）。"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / "config/dev/.env", override=True)

BASE = os.getenv("VERIFY_API_BASE", "http://127.0.0.1:8001/api/v1")
USER = os.getenv("VERIFY_ADMIN_USER", "admin")
PASS = os.getenv("VERIFY_ADMIN_PASS", "admin123")


class Check:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.skipped: list[str] = []

    def ok(self, name: str, detail: str = "") -> None:
        self.passed.append(f"{name}" + (f" — {detail}" if detail else ""))

    def fail(self, name: str, detail: str) -> None:
        self.failed.append(f"{name}: {detail}")

    def skip(self, name: str, reason: str) -> None:
        self.skipped.append(f"{name}: {reason}")


def _data(resp: httpx.Response) -> dict:
    body = resp.json()
    if isinstance(body, dict) and "data" in body:
        return body.get("data") or {}
    return body if isinstance(body, dict) else {}


def main() -> int:
    c = Check()
    logger.info('=== 功能检验 @ {BASE} ===\\n', BASE)

    with httpx.Client(timeout=120.0) as client:
        # 1. 登录
        r = client.post(
            f"{BASE}/auth/login",
            json={"username_or_email": USER, "password": PASS},
        )
        if r.status_code != 200:
            c.fail("登录", r.text[:200])
            return _report(c)
        token = _data(r).get("access_token") or _data(r).get("token")
        if not token:
            c.fail("登录", "无 access_token")
            return _report(c)
        c.ok("登录")
        h = {"Authorization": f"Bearer {token}"}

        # 2. 多媒体工厂概览
        r = client.get(f"{BASE}/media-factory/", headers=h)
        ov = _data(r)
        if r.status_code == 200 and ov.get("mock_render") is True:
            c.ok("多媒体工厂概览", f"mock=True retention={ov.get('media_retention_hours')}h")
        else:
            c.fail("多媒体工厂概览", f"status={r.status_code} mock={ov.get('mock_render')}")

        # 3. 创建并同步渲染
        script = "镜头1 | 检验功能测试画面 | 旁白：系统检验\n镜头2 | 产品展示 | 旁白：功能齐全"
        r = client.post(
            f"{BASE}/media-factory/generate",
            headers=h,
            json={
                "script": script,
                "title": "功能检验",
                "resolution": "720p",
                "aspect": "16:9",
                "auto_render": False,
            },
        )
        if r.status_code != 200:
            c.fail("创建渲染任务", r.text[:200])
            return _report(c)
        task = _data(r)
        task_id = task.get("id")
        if not task_id:
            c.fail("创建渲染任务", "无 task id")
            return _report(c)
        c.ok("创建渲染任务", task_id[:8])

        r = client.post(f"{BASE}/media-factory/tasks/{task_id}/run-sync", headers=h)
        task = _data(r)
        if task.get("raw_status") != "done" or not task.get("result_url"):
            c.fail("同步渲染", f"status={task.get('raw_status')} err={task.get('error_message')}")
            return _report(c)
        c.ok("同步渲染", task.get("result_url", ""))

        # 4. 保留策略字段
        if task.get("retention_hours") and task.get("expires_at"):
            c.ok("保留策略", f"{task.get('retention_hours')}h / purge_in={task.get('seconds_until_purge')}s")
        else:
            c.fail("保留策略", json.dumps({k: task.get(k) for k in ('retention_hours', 'expires_at', 'purge_at')}, ensure_ascii=False))

        # 5. 剪辑调试 GET
        r = client.get(f"{BASE}/media-factory/tasks/{task_id}/edit", headers=h)
        edit = _data(r)
        dur = float(edit.get("source_duration_sec") or 0)
        if r.status_code == 200 and dur > 0 and edit.get("shots"):
            c.ok("剪辑状态", f"duration={dur}s shots={len(edit.get('shots', []))}")
        else:
            c.fail("剪辑状态", f"status={r.status_code} dur={dur}")

        # 6. 应用剪辑
        end = min(1.5, dur)
        r = client.post(
            f"{BASE}/media-factory/tasks/{task_id}/clip",
            headers=h,
            json={"start_sec": 0, "end_sec": end},
        )
        clipped = _data(r)
        if r.status_code == 200 and clipped.get("edited_result_url"):
            c.ok("视频剪辑", clipped.get("edited_result_url", ""))
        else:
            c.fail("视频剪辑", r.text[:200])

        # 7. 保存脚本
        shots = edit.get("shots") or []
        if shots:
            shots[0]["narration"] = "旁白：检验已修改"
        r = client.put(
            f"{BASE}/media-factory/tasks/{task_id}/script",
            headers=h,
            json={"script": script, "shots": shots},
        )
        if r.status_code == 200:
            r2 = client.get(f"{BASE}/media-factory/tasks/{task_id}/edit", headers=h)
            saved_script = _data(r2).get("script") or ""
            if "检验已修改" in saved_script:
                c.ok("脚本保存")
            else:
                c.fail("脚本保存", "保存后脚本未更新")
        else:
            c.fail("脚本保存", r.text[:200])

        # 8. Handoff
        r = client.post(
            f"{BASE}/media-factory/tasks/{task_id}/handoff",
            headers=h,
            json={"action": "downloaded"},
        )
        if r.status_code == 200 and _data(r).get("handoff_type") == "downloaded":
            c.ok("Handoff 登记")
        else:
            c.fail("Handoff 登记", r.text[:200])

        # 9. 场景模型（超管）
        r = client.get(f"{BASE}/super-admin/ai-config/nvidia/scenarios", headers=h)
        sc = _data(r)
        if r.status_code == 200 and sc.get("groups"):
            c.ok("场景模型配置", f"{len(sc.get('groups', []))} 组")
        else:
            c.fail("场景模型配置", f"status={r.status_code}")

        # 10. 场景健康
        r = client.get(f"{BASE}/super-admin/ai-config/nvidia/scenarios/health", headers=h)
        health = _data(r)
        if r.status_code == 200 and "healthy_count" in health:
            c.ok("场景健康检查", f"{health.get('healthy_count')}/{health.get('total')}")
        else:
            c.fail("场景健康检查", r.text[:200])

        r = client.get(f"{BASE}/super-admin/ai-config/nvidia/scenarios/health/latest", headers=h)
        if r.status_code == 200:
            c.ok("健康快照 latest", "有数据" if _data(r) else "尚无快照")
        else:
            c.fail("健康快照 latest", r.text[:200])

        # 11. Ops 清理状态
        r = client.get(f"{BASE}/ops/media-cleanup/status", headers=h)
        if r.status_code == 200:
            c.ok("视频清理调度状态", f"running={_data(r).get('running')}")
        else:
            c.fail("视频清理调度状态", r.text[:200])

        # 12. 渲染队列
        r = client.get(f"{BASE}/media-factory/render-queue", headers=h)
        rq = _data(r)
        items = rq.get("list") or rq.get("items") or []
        if r.status_code == 200 and isinstance(items, list):
            c.ok("渲染队列", f"{len(items)} 条")
        else:
            c.fail("渲染队列", r.text[:200])

        # 13. 重渲（可选，不等待完成）
        r = client.post(
            f"{BASE}/media-factory/tasks/{task_id}/re-render",
            headers=h,
            json={"script": script, "auto_render": False},
        )
        if r.status_code == 200 and _data(r).get("raw_status") == "queued":
            c.ok("重新渲染入队")
        else:
            c.fail("重新渲染入队", r.text[:200])

        # 14. 租户场景 API（admin 无租户时预期 403）
        r = client.get(f"{BASE}/tenants/self/ai-scenarios", headers=h)
        if r.status_code == 200:
            c.ok("租户场景 API")
        elif r.status_code in (403, 400):
            c.skip("租户场景 API", "当前 admin 无绑定租户（预期）")
        else:
            c.fail("租户场景 API", f"status={r.status_code}")

        # 15. 前端路由文件存在性（静态）
        fe = BACKEND_ROOT.parent / "frontend" / "admin" / "src" / "views"
        pages = [
            fe / "admin" / "ai-center" / "article-to-video.vue",
            fe / "admin" / "ai-center" / "scenario-models.vue",
            fe / "client" / "ai-scenarios.vue",
            fe / "media-factory" / "render-queue.vue",
        ]
        missing = [str(p.name) for p in pages if not p.exists()]
        if not missing:
            c.ok("前端页面", "article-to-video / scenario-models / ai-scenarios / render-queue")
        else:
            c.fail("前端页面", f"缺失: {missing}")

    return _report(c)


def _report(c: Check) -> int:
    logger.info('\\n--- 通过 ---')
    for line in c.passed:
        logger.info('  ✓ {line}', line)
    if c.skipped:
        logger.info('\\n--- 跳过 ---')
        for line in c.skipped:
            logger.info('  ○ {line}', line)
    if c.failed:
        logger.info('\\n--- 失败 ---')
        for line in c.failed:
            logger.info('  ✗ {line}', line)
    logger.info('\\n合计: {len(c.passed)} 通过, {len(c.skipped)} 跳过, {len(c.failed)} 失败', len(c.passed), len(c.skipped), len(c.failed))
    return 1 if c.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

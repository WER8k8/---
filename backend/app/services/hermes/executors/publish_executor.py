"""Publish Executor Plugin — 多平台内容分发。

⚠️ 重要：本插件**刻意不使用** `PublishDispatchService.distribute`
   —— 该方法只是对 channels 循环计数并恒返回 status="success"，**未调用任何发布器**（假成功）。
   真正的发布能力在 `services/publish_service.py` 的 8 个 Publisher 类，
   经 `PublishService.publish(platform_id, content)` 暴露，未接入的平台走
   `UnimplementedPublisher` **明确失败**（不冒充成功）。

能力：
    publish.multi    —— 多平台分发（channels 列表）
    publish.single   —— 单平台分发

输入：
    {"channels": ["wechat", "zhihu"], "title": "...", "body": "...", "media_urls": [...]}
    {"platform": "wechat", "title": "...", "body": "..."}   # 单平台

输出：
    {"results": {platform: {status, platform_post_url, error_message}},
     "succeeded": n, "failed": n, "not_configured": n, "summary": "一句话人话"}

三分法（2026-09-10 实测后确立，防止"环境没配"被误判成"业务失败"）：
    · 真发成功            → succeeded，节点 succeeded
    · 渠道未配置 / 未接入  → not_configured，**不发请求**，节点 skipped（原因写进 output）
    · 配了但真发失败       → failed，节点 failed
    全渠道都未配置时节点记 skipped（不算成功、也不把整条链判死），原因逐平台留痕。
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"publish.multi", "publish.single", "default"})

# 「环境没配好」的两个错误码 —— 命中即记 skipped，不记业务失败
_UNCONFIGURED_CODES = frozenset({"PLATFORM_NOT_CONFIGURED", "PLATFORM_NOT_IMPLEMENTED"})


class PublishExecutor(BaseExecutor):
    """多平台分发执行器（走真发布器）。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "publish"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"publish 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})

        # 组装渠道列表
        channels: list[str] = []
        raw = params.get("channels")
        if isinstance(raw, str):
            channels = [c.strip() for c in raw.split(",") if c.strip()]
        elif isinstance(raw, list):
            channels = [str(c).strip() for c in raw if str(c).strip()]
        single = params.get("platform")
        if single and not channels:
            channels = [str(single).strip()]
        if not channels:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_channels: 需提供 channels（列表）或 platform（单平台）",
            )

        content: dict[str, Any] = {
            k: params.get(k)
            for k in ("title", "body", "summary", "media_urls", "video_url", "cover_url", "url")
            if params.get(k) is not None
        }
        if not content:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_content: 需提供 title/body 等至少一项内容字段",
            )

        try:
            from app.services.publish_capability_registry import (
                PLATFORM_NOT_CONFIGURED,
                PLATFORM_NOT_IMPLEMENTED,
                normalize_publish_result,
                publish_block_reason,
            )
            from app.services.publish_service import PublishService

            # 复用编排会话读平台目录（不传 db 会自开短会话，同一条链上多一次无谓连接）
            svc = PublishService(context.db)
            unconfigured_codes = frozenset({PLATFORM_NOT_CONFIGURED, PLATFORM_NOT_IMPLEMENTED})
            results: dict[str, Any] = {}
            succeeded = failed = not_configured = 0
            for pid in channels:
                cfg = svc.find_platform_config(pid)
                # 预检：这类渠道压根没有可用发布器 → 一次请求都不该发，直接记"未配置"
                blocked = self._preflight_block_reason(cfg, pid, content)
                if blocked:
                    results[pid] = normalize_publish_result(
                        {
                            "status": "failed",
                            "error_code": PLATFORM_NOT_IMPLEMENTED,
                            "configured": False,
                            "error_message": blocked,
                        }
                    )
                    not_configured += 1
                    continue
                try:
                    r = await svc.publish(pid, content)
                    r = normalize_publish_result(r) if r else {
                        "status": "failed",
                        "error_code": PLATFORM_NOT_CONFIGURED,
                        "error_message": "发布器返回空结果",
                    }
                except Exception as exc:  # noqa: BLE001 — 单平台异常不阻断其他平台
                    logger.exception("PublishExecutor: 平台 %s 发布异常", pid)
                    r = {
                        "status": "failed",
                        "error_code": "PUBLISHER_EXCEPTION",
                        "error_message": f"{type(exc).__name__}: {exc}",
                    }
                results[pid] = r
                code = str(r.get("error_code") or "")
                if str(r.get("status", "")).lower() == "success":
                    succeeded += 1
                elif code in unconfigured_codes:
                    not_configured += 1
                else:
                    failed += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("PublishExecutor 初始化失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        not_configured_detail = {
            pid: {
                "error_code": str(r.get("error_code") or ""),
                "error_message": str(r.get("error_message") or ""),
                "missing_credentials": r.get("missing_credentials") or [],
            }
            for pid, r in results.items()
            if str(r.get("error_code") or "") in unconfigured_codes
        }
        output = {
            "executor": self.get_executor_name(),
            "channels": channels,
            "results": results,
            "succeeded": succeeded,
            "failed": failed,
            "not_configured": not_configured,
            "not_configured_detail": not_configured_detail,
            # 全失败即节点失败；部分成功如实标注，不谎报"全部成功"
            "partial": 0 < succeeded < len(channels),
        }
        output["summary"] = self._summarize(
            channels=channels,
            succeeded=succeeded,
            failed=failed,
            not_configured=not_configured,
            detail=not_configured_detail,
        )

        if succeeded > 0:
            status = "succeeded"
            error = (
                None
                if failed == 0
                else self._failure_message(
                    results, failed=failed, not_configured=not_configured
                )
            )
        elif failed > 0:
            status = "failed"
            error = self._failure_message(
                results, failed=failed, not_configured=not_configured
            )
        elif not_configured > 0:
            # 一个渠道都没配齐 → 属环境未完成，不是业务失败：记 skipped，原因留在 output
            status = "skipped"
            error = None
        else:
            status = "failed"
            error = "无渠道结果（不应发生）"
        return ExecutorResult(node_id=node.id, status=status, output=output, error=error)

    @staticmethod
    def _preflight_block_reason(cfg, pid: str, content: dict) -> str:
        """这一渠道是否压根不必尝试发布（返回拦下它的人话原因，空串表示可以继续发）。

        发布器键优先取库里的 publisher_key，取不到才退回入参原值 ——
        channels 里可能写的是显示名（"微信公众号"），直接当键查会误判成"未接入"。
        """
        from app.services.publish_capability_registry import publish_block_reason

        return publish_block_reason(
            platform_name=(cfg or {}).get("name"),
            publisher_key=(cfg or {}).get("publisher_key") or pid,
            content=content,
        )

    @staticmethod
    def _summarize(
        *,
        channels: list,
        succeeded: int,
        failed: int,
        not_configured: int,
        detail: dict,
    ) -> str:
        """给人看的一句话（落进 ai_tasks.output_json，排障时不用再翻 results）。"""
        total = len(channels)
        if succeeded:
            text = f"{succeeded}/{total} 个渠道真发成功"
            if failed:
                text += f"，{failed} 个失败"
            if not_configured:
                text += f"，{not_configured} 个未配置"
            return text
        if not_configured and not failed:
            first = next(iter(detail.values()), {}) if detail else {}
            return (
                f"{not_configured}/{total} 个渠道未配置或未接入，未发起任何真实请求"
                f"（示例原因：{first.get('error_message') or '未知'}）"
            )
        return f"全部 {total} 个渠道发布失败，成功 0"

    @staticmethod
    def _failure_message(results: dict, *, failed: int, not_configured: int) -> str:
        """把逐平台原因拼进 error，避免"所有平台发布均失败"这种无信息量结论。"""
        parts = []
        for pid, r in results.items():
            if str(r.get("status", "")).lower() == "success":
                continue
            if str(r.get("error_code") or "") in (
                "PLATFORM_NOT_CONFIGURED",
                "PLATFORM_NOT_IMPLEMENTED",
            ):
                continue  # 未配置的单列在 not_configured_detail，不混进失败原因
            parts.append(f"{pid}：{r.get('error_message') or '无错误信息'}")
        head = f"{failed} 个渠道真发失败"
        if not_configured:
            head += f"（另有 {not_configured} 个未配置）"
        if not parts:
            return head
        return f"{head} ｜ " + "；".join(parts)[:900]


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "publish.multi": {
                "desc": "多平台分发（走真发布器；8 个平台已接入，其余按「未接入」记 skipped）",
                "input": ["channels", "title", "body", "media_urls", "url"],
                "output": [
                    "results",
                    "succeeded",
                    "failed",
                    "not_configured",
                    "not_configured_detail",
                    "partial",
                    "summary",
                ],
                "cost": {"tokens": 0, "seconds": 120},
                "needs_approval": True,
            },
            "publish.single": {"desc": "单平台分发", "input": ["platform", "title", "body"]},
        }


ExecutorRegistry.register(PublishExecutor())

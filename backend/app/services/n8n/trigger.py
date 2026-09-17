# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""n8n 工作流触发器。

向 n8n 发送 Webhook 请求触发工作流，支持：
- Celery 异步执行
- 失败重试 3 次，指数退避（1s → 2s → 4s）
- 触发日志记录
- 超时控制（默认 30s）
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

import httpx
from celery import shared_task

from app.services.n8n.workflow_registry import get_workflow_registry, ensure_builtin_workflows

log = logging.getLogger(__name__)

# 触发超时（秒）
DEFAULT_TIMEOUT = 30.0
# 最大重试次数
MAX_RETRIES = 3
# 退避基数（秒）：1, 2, 4
BACKOFF_BASE = 1.0


class N8nTriggerService:
    """n8n 工作流触发服务。

    负责向 n8n webhook endpoint 发送 HTTP POST 请求触发工作流。
    支持同步和异步调用。

    用法:
        service = N8nTriggerService()
        result = await service.trigger("wf_001", {"product_id": "123"})
        # 或同步调用
        result = service.trigger_sync("wf_001", {"product_id": "123"})
    """
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param timeout: 参数 timeout
        :param max_retries: 参数 max_retries
        :return: 返回处理结果。
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def trigger(
        self,
        workflow_id: str,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """异步触发 n8n 工作流。

        Args:
            workflow_id: 工作流 ID（对应 workflow_registry 中的注册记录）。
            payload: 发送给 n8n 的 JSON 数据。
            headers: 可选的额外请求头。

        Returns:
            触发结果字典：{"success": bool, "workflow_id": str, "status_code": int, "response": any}

        Raises:
            ValueError: 工作流不存在或已禁用。
        """
        # 幂等注册内建工作流（如 site_built_notify），确保 web 与 worker 进程均可解析
        ensure_builtin_workflows()
        registry = get_workflow_registry()
        record = registry.get(workflow_id)
        if record is None:
            raise ValueError(f"工作流 {workflow_id} 未注册")
        if not record.enabled:
            raise ValueError(f"工作流 {workflow_id} 已禁用")

        endpoint, request_headers = await self._build_n8n_request_headers(headers, record, workflow_id)
        last_error: Optional[Exception] = None
        start_time = time.monotonic()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(
                        endpoint,
                        json=payload,
                        headers=request_headers,
                    )
                    elapsed = time.monotonic() - start_time
                    if response.status_code < 400:
                        log.info(
                            "n8n 工作流触发成功: %s (attempt=%d, elapsed=%.2fs, status=%d)",
                            workflow_id, attempt + 1, elapsed, response.status_code,
                        )
                        registry.record_trigger(workflow_id, success=True)
                        return {
                            "success": True,
                            "workflow_id": workflow_id,
                            "status_code": response.status_code,
                            "response": self._safe_parse_response(response),
                            "attempts": attempt + 1,
                            "elapsed_seconds": round(elapsed, 3),
                        }
                    else:
                        log.warning(
                            "n8n 工作流触发返回错误: %s (attempt=%d, status=%d, body=%s)",
                            workflow_id, attempt + 1, response.status_code,
                            response.text[:200],
                        )
                        last_error = RuntimeError(
                            f"n8n 返回 HTTP {response.status_code}: {response.text[:200]}"
                        )
                except httpx.TimeoutException as exc:
                    elapsed = time.monotonic() - start_time
                    log.warning(
                        "n8n 工作流触发超时: %s (attempt=%d, elapsed=%.2fs)",
                        workflow_id, attempt + 1, elapsed,
                    )
                    last_error = exc
                except httpx.RequestError as exc:
                    elapsed = time.monotonic() - start_time
                    log.warning(
                        "n8n 工作流触发请求异常: %s (attempt=%d, error=%s)",
                        workflow_id, attempt + 1, exc,
                    )
                    last_error = exc

                # 指数退避
                if attempt < self.max_retries:
                    backoff = BACKOFF_BASE * (2 ** attempt)
                    log.info("n8n 触发退避重试: %s (%.1fs 后第 %d 次重试)",
                             workflow_id, backoff, attempt + 2)
                    await asyncio.sleep(backoff)

        return await self._finalize_n8n_failure(last_error, registry, start_time, workflow_id)


    async def _build_n8n_request_headers(self, headers, record, workflow_id):
        """_build_n8n_request_headers。

        参数说明：
        :param self: 参数 self
        :param headers: 参数 headers
        :param record: 参数 record
        :param workflow_id: 参数 workflow_id
        :return: 返回处理结果。
        """
        endpoint = record.endpoint
        auth_config = record.auth_config or {}
        # 构建请求头
        request_headers = {

            "Content-Type": "application/json",
            "X-N8n-Trigger-Source": "uj-backend",
            "X-N8n-Workflow-Id": workflow_id,

        }
        # 添加认证头
        if auth_config.get("auth_type") == "header":

            header_name = auth_config.get("header_name", "X-Api-Key")
            header_value = auth_config.get("header_value", "")
            request_headers[header_name] = header_value

        if headers:

            request_headers.update(headers)

        return (endpoint, request_headers)


    async def _finalize_n8n_failure(self, last_error, registry, start_time, workflow_id):
        """_finalize_n8n_failure。

        参数说明：
        :param self: 参数 self
        :param last_error: 参数 last_error
        :param registry: 参数 registry
        :param start_time: 参数 start_time
        :param workflow_id: 参数 workflow_id
        :return: 返回处理结果。
        """
        # 全部重试失败
        elapsed = time.monotonic() - start_time
        log.error(

            "n8n 工作流触发最终失败: %s (attempts=%d, elapsed=%.2fs, error=%s)",
            workflow_id, self.max_retries + 1, elapsed, last_error,

        )
        registry.record_trigger(workflow_id, success=False)
        return {

            "success": False,
            "workflow_id": workflow_id,
            "status_code": 0,
            "error": str(last_error) if last_error else "Unknown error",
            "attempts": self.max_retries + 1,
            "elapsed_seconds": round(elapsed, 3),

        }


    def trigger_sync(
        self,
        workflow_id: str,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """同步触发 n8n 工作流（用于非异步上下文）。"""
        try:
            loop = asyncio.get_running_loop()
            # 已在事件循环中，创建新线程执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.trigger(workflow_id, payload, headers=headers),
                )
                return future.result()
        except RuntimeError:
            # 无事件循环，直接运行
            return asyncio.run(self.trigger(workflow_id, payload, headers=headers))

    @staticmethod
    def _safe_parse_response(response: httpx.Response) -> Any:
        """安全解析响应体。"""
        try:
            return response.json()
        except Exception:
            return response.text


# ============================================================
# Celery 异步任务
# ============================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=2)
def trigger_n8n_workflow(
    self,
    workflow_id: str,
    payload: dict[str, Any],
    *,
    headers: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Celery 异步任务：触发 n8n 工作流。

    使用 bind=True 获取 self，支持 self.retry() 指数退避。

    Args:
        workflow_id: 工作流 ID。
        payload: 发送的 JSON 数据。
        headers: 可选的额外请求头。

    Returns:
        触发结果字典。

    Raises:
        self.retry: 失败时自动重试。
    """
    service = N8nTriggerService()
    try:
        result = asyncio.run(
            service.trigger(workflow_id, payload, headers=headers)
        )
        if not result["success"]:
            # 触发失败，尝试重试
            raise RuntimeError(result.get("error", "触发失败"))
        return result
    except ValueError:
        # 工作流不存在或已禁用，不再重试
        raise
    except Exception as exc:
        log.warning(
            "Celery n8n 触发任务失败 (attempt=%d): %s",
            self.request.retries + 1, exc,
        )
        raise self.retry(exc=exc)

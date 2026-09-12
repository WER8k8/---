import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, Response
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import SessionLocal
from app.core.security import resolve_user_from_request
from app.models.user import OperationLog


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件 - 自动记录所有API请求"""
    async def dispatch(self, request: Request, call_next) -> Response:
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        # 排除健康检查和静态资源
        path = request.url.path
        if path.startswith(
                "/health") or path.startswith("/static") or path.startswith("/uploads"):
            return await call_next(request)

        start_time = datetime.now(timezone.utc)
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        # 获取用户信息
        user_id = None
        db = SessionLocal()
        try:
            user = resolve_user_from_request(request, db)
            if user:
                user_id = str(user.id)
        except Exception:
            pass
        finally:
            db.close()

        # 缓存请求体（避免 consume 原始 body）
        request_body = {}
        body_bytes = b""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body_bytes = await request.body()
                request_body = json.loads(body_bytes) if body_bytes else {}
                request_body = self.sanitize_data(request_body)
        except Exception:
            pass

        # 执行请求
        response = await call_next(request)
        # 记录审计日志
        db = SessionLocal()
        try:
            duration = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()
            log_entry = OperationLog(
                user_id=user_id,
                action=request.method,
                resource_type=path.split("/")[2] if len(path.split("/")) > 2 else "unknown",
                resource_id=path.split("/")[3] if len(path.split("/")) > 3 else None,
                detail=json.dumps(
                    {
                        "path": path,
                        "query_params": dict(request.query_params),
                        "request_body": request_body,
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000),
                        "user_agent": user_agent[:200],
                    }
                ),
                ip_address=client_ip,
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            pass
        finally:
            db.close()

        return response

    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip
        return request.client.host if request.client else "unknown"

    def sanitize_data(self, data: dict) -> dict:
        """过滤敏感数据"""
        sensitive_fields = ["password", "token", "secret", "key", "credential"]
        result = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                result[key] = "***"
            elif isinstance(value, dict):
                result[key] = self.sanitize_data(value)
            elif isinstance(value, list):
                result[key] = [
                    self.sanitize_data(item) if isinstance(
                        item, dict) else item for item in value]
            else:
                result[key] = value
        return result

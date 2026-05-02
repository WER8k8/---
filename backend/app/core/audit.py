import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import OperationLog
from app.core.security import get_current_user_optional


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件 - 自动记录所有API请求"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # 排除健康检查和静态资源
        path = request.url.path
        if path.startswith("/health") or path.startswith("/static") or path.startswith("/uploads"):
            return await call_next(request)
        
        start_time = datetime.now(timezone.utc)
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 获取用户信息
        user_id = None
        try:
            db = SessionLocal()
            user = await get_current_user_optional(request=request, db=db)
            if user:
                user_id = str(user.id)
            db.close()
        except Exception:
            pass
        
        # 获取请求体
        request_body = {}
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                request_body = await request.json()
                # 过滤敏感信息
                request_body = self.sanitize_data(request_body)
        except Exception:
            pass
        
        # 执行请求
        response = await call_next(request)
        
        # 记录审计日志
        try:
            db = SessionLocal()
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            log_entry = OperationLog(
                user_id=user_id,
                action=request.method,
                resource_type=path.split("/")[2] if len(path.split("/")) > 2 else "unknown",
                resource_id=path.split("/")[3] if len(path.split("/")) > 3 else None,
                detail=json.dumps({
                    "path": path,
                    "query_params": dict(request.query_params),
                    "request_body": request_body,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000),
                    "user_agent": user_agent[:200],
                }),
                ip_address=client_ip,
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            # 日志记录失败不影响主流程
            pass
        
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
                result[key] = [self.sanitize_data(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        return result

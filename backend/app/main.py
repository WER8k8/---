import os
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.audit import AuditMiddleware
from app.core.performance_middleware import PerformanceMiddleware
from app.services.cache_service import ResponseCacheMiddleware
from app.api.v1 import system_routes as system, products, content, seo, case_studies, inquiries, analytics, users
from app.api.v1 import sitemap
from app.api.v1.system import performance as performance_api

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="轻集料混凝土企业官网 SEO 智能运营系统 API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limit_map = defaultdict(list)
        self.RATE_LIMIT = max_requests
        self.WINDOW_SECONDS = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        now = time.time()
        window_start = now - self.WINDOW_SECONDS
        self.rate_limit_map[client_ip] = [t for t in self.rate_limit_map[client_ip] if t > window_start]
        if len(self.rate_limit_map[client_ip]) >= self.RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
            )
        self.rate_limit_map[client_ip].append(now)
        response = await call_next(request)
        return response

    def get_client_ip(self, request: Request) -> str:
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip
        return request.client.host if request.client else "unknown"


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            origin = request.headers.get("origin", "").strip()
            referer = request.headers.get("referer", "").strip()
            
            path = str(request.url.path)
            
            # 允许登录接口跳过CSRF验证
            if path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/system/login") or path.startswith("/api/v1/system/register"):
                response = await call_next(request)
                return response
            
            # 开发环境允许localhost请求跳过CSRF验证
            if settings.DEBUG:
                client_host = request.client.host if request.client else ""
                if client_host in ("localhost", "127.0.0.1", "::1"):
                    # 允许所有 localhost 端口的请求
                    if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
                        response = await call_next(request)
                        return response
            
            if not origin:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF验证失败：缺少Origin请求头"},
                )
            
            allowed = False
            for allowed_origin in settings.CORS_ORIGINS:
                if origin == allowed_origin:
                    allowed = True
                    break
            
            if not allowed:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF验证失败：不被允许的请求来源"},
                )
            
            if referer:
                referer_origin = ""
                if referer.startswith("http://"):
                    referer_origin = "http://" + referer[7:].split("/")[0]
                elif referer.startswith("https://"):
                    referer_origin = "https://" + referer[8:].split("/")[0]
                
                if referer_origin and not any(
                    referer_origin == allowed_origin or referer.startswith(allowed_origin)
                    for allowed_origin in settings.CORS_ORIGINS
                ):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF验证失败：Referer与Origin不匹配"},
                    )
                    
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 基础安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=(), accelerometer=()"
        
        # 内容安全策略 (CSP) - 开发环境放宽限制
        if settings.DEBUG:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https://*.nvidia.com https://api.openai.com http://localhost:* http://127.0.0.1:*; "
                "object-src 'none'; "
                "frame-src 'none'; "
                "form-action 'self'; "
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https://*.nvidia.com https://api.openai.com; "
                "object-src 'none'; "
                "frame-src 'none'; "
                "form-action 'self'; "
                "upgrade-insecure-requests;"
            )
        
        # 跨域嵌入器策略 - 开发环境允许跨域
        if settings.DEBUG:
            response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
            response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        else:
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(ResponseCacheMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type"],
    max_age=600,
)

app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)
app.add_middleware(CsrfProtectionMiddleware)
app.add_middleware(AuditMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

uploads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

app.include_router(system.router, prefix=f"{settings.API_V1_PREFIX}/system", tags=["系统管理"])
app.include_router(performance_api.router, prefix=f"{settings.API_V1_PREFIX}", tags=["性能与安全"])
app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["产品管理"])
app.include_router(content.router, prefix=f"{settings.API_V1_PREFIX}/content", tags=["内容管理"])
app.include_router(seo.router, prefix=f"{settings.API_V1_PREFIX}/seo", tags=["SEO优化"])
app.include_router(case_studies.router, prefix=f"{settings.API_V1_PREFIX}/cases", tags=["案例管理"])
app.include_router(inquiries.router, prefix=f"{settings.API_V1_PREFIX}/inquiries", tags=["询盘管理"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["数据分析"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}", tags=["用户管理"])
app.include_router(sitemap.router, tags=["站点地图"])

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"✅ {settings.APP_NAME} 启动成功")
    logger.info(f"📌 API版本: {settings.API_V1_PREFIX}")
    logger.info(f"🔧 调试模式: {'开启' if settings.DEBUG else '关闭'}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🛑 {settings.APP_NAME} 正在关闭...")

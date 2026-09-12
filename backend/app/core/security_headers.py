"""
HTTP安全响应头中间件
添加标准安全响应头防止常见Web攻击

OWASP 推荐安全头:
- Content-Security-Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security (HSTS)
- X-XSS-Protection (旧版浏览器)
- Referrer-Policy
- Permissions-Policy
- X-Permitted-Cross-Domain-Policies
- Cross-Origin-Embedder-Policy
- Cross-Origin-Opener-Policy
- Cross-Origin-Resource-Policy
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.middleware_fastlane import is_probe_or_static


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    HTML页面安全响应头中间件

    添加以下安全头：
    - X-Content-Type-Options: nosniff — 防止MIME类型嗅探
    - X-Frame-Options: DENY — 防止点击劫持
    - X-XSS-Protection: 1; mode=block — XSS过滤（旧版浏览器）
    - Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
    - Content-Security-Policy: 严格CSP策略
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: 限制敏感API
    - X-Permitted-Cross-Domain-Policies: none — 防止跨域策略文件滥用
    - Cross-Origin-Opener-Policy: same-origin — 防止跨域信息泄露
    - Cross-Origin-Resource-Policy: same-origin — 防止跨域资源加载
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        response = await call_next(request)
        # 只对HTML响应添加安全头（避免影响API/静态资源）
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type or not content_type:
            # X-Content-Type-Options: 防止MIME类型嗅探
            response.headers["X-Content-Type-Options"] = "nosniff"
            # X-Frame-Options: 防止点击劫持
            response.headers["X-Frame-Options"] = "DENY"
            # X-XSS-Protection: XSS过滤（现代浏览器已忽略，但旧版需要）
            response.headers["X-XSS-Protection"] = "1; mode=block"
            # Content-Security-Policy: 严格CSP策略
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https: wss:; "
                "media-src 'self'; "
                "object-src 'none'; "
                "frame-src 'self'; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                "upgrade-insecure-requests; "
                "block-all-mixed-content"
            )
            # X-Request-ID: 请求追踪
            import uuid
            if "X-Request-ID" not in response.headers:
                response.headers["X-Request-ID"] = str(uuid.uuid4())

        # 所有响应都添加HSTS（强制HTTPS）
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        # Referrer策略: 跨域时只发送源
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # 权限策略: 限制浏览器功能
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), bluetooth=(), "
            "magnetometer=(), gyroscope=(), "
            "fullscreen=(self), "
            "display-capture=()"
        )
        # 跨域策略
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        # 跨域隔离策略
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        # 移除敏感信息泄露头
        for sensitive_header in ["Server", "X-Powered-By", "X-AspNet-Version",
                                 "X-AspNetMvc-Version"]:
            if sensitive_header in response.headers:
                del response.headers[sensitive_header]

        return response


class APISecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    API专用安全响应头中间件

    针对API响应优化的安全头配置：
    - 更严格的CSP（API不应执行脚本）
    - 强制禁止缓存敏感API数据
    - frame-ancestors 'none' 防止API被嵌入iframe
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        if is_probe_or_static(request.url.path):
            return await call_next(request)

        response = await call_next(request)
        # X-Content-Type-Options: 所有API响应都添加
        response.headers["X-Content-Type-Options"] = "nosniff"
        # X-Frame-Options: 防止API被嵌入iframe
        response.headers["X-Frame-Options"] = "DENY"
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Cache-Control: 防止敏感API数据被缓存
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # HSTS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        # Content-Security-Policy（API使用更严格的CSP，禁止脚本执行）
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "script-src 'self'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests"
        )
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions-Policy: API不应需要任何权限
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), bluetooth=()"
        )
        # 跨域策略
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        # 移除敏感头
        for sensitive_header in ["Server", "X-Powered-By", "X-AspNet-Version",
                                 "X-AspNetMvc-Version"]:
            if sensitive_header in response.headers:
                del response.headers[sensitive_header]

        # X-Request-ID: 请求追踪
        import uuid
        if "X-Request-ID" not in response.headers:
            response.headers["X-Request-ID"] = str(uuid.uuid4())

        return response

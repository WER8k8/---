"""
WAF防火墙规则配置
提供SQL注入、XSS、路径遍历等常见攻击防护
"""

import re
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


class WAFMiddleware(BaseHTTPMiddleware):
    """Web应用防火墙中间件"""
    
    # SQL注入特征
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC)\b)",
        r"(--|;|\/\*|\*\/|@@|@)",
        r"(CHAR\(|CONCAT\(|GROUP_CONCAT\(|LOAD_FILE\(|INTO\s+OUTFILE)",
        r"(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)",
        r"(BENCHMARK|SLEEP|WAITFOR\s+DELAY)",
        r"(EXEC\s*\(|EXECUTE\s+IMMEDIATE)",
    ]
    
    # XSS攻击特征
    XSS_PATTERNS = [
        r"(<script|</script|javascript:|on\w+\s*=)",
        r"(eval\(|alert\(|prompt\(|confirm\()",
        r"(document\.cookie|document\.write|window\.location)",
        r"(<iframe|<object|<embed|<form)",
        r"(expression\(|url\(|import\s)",
    ]
    
    # 路径遍历特征
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\./|\.\.\\)",
        r"(%2e%2e%2f|%2e%2e/|\.\.%2f|%2e%2e%5c)",
        r"(/etc/passwd|/etc/shadow|/proc/self)",
        r"(boot\.ini|win\.ini|web\.config)",
    ]
    
    # 命令注入特征
    COMMAND_INJECTION_PATTERNS = [
        r"(\||;|&&|\|\||`|\$\()",
        r"(\/bin\/sh|\/bin\/bash|cmd\.exe|powershell)",
        r"(wget\s|curl\s|nc\s|netcat\s|bash\s-i)",
        r"(\/dev\/tcp|\/dev\/udp)",
    ]
    
    # 编译正则表达式
    SQL_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in SQL_INJECTION_PATTERNS]
    XSS_RE = [re.compile(p, re.IGNORECASE) for p in XSS_PATTERNS]
    PATH_TRAVERSAL_RE = [re.compile(p, re.IGNORECASE) for p in PATH_TRAVERSAL_PATTERNS]
    COMMAND_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in COMMAND_INJECTION_PATTERNS]
    
    # 白名单路径前缀（跳过WAF检查）
    WHITELIST_PATH_PREFIXES = [
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/openapi.json",  # 添加根路径openapi
        "/health",
        "/api/v1/health",
        "/api/v1/system/login",
        "/api/v1/system/register",
        "/api/v1/seo/",
        "/api/v1/products",
        "/api/v1/content/",
        "/api/v1/cases",
        "/api/v1/inquiries",
        "/api/v1/users",
        "/api/v1/system/audit/",
        "/api/v1/system/contact",
        "/api/v1/analytics/",
        "/api/v1/sitemap",
        "/api/v1/metrics",
        "/api/v1/performance",
        "/uploads",
        "/",  # 添加首页
    ]
    
    async def dispatch(self, request: Request, call_next):
        path = str(request.url.path)
        
        # 跳过白名单路径（前缀匹配）
        if any(path.startswith(prefix) for prefix in self.WHITELIST_PATH_PREFIXES):
            return await call_next(request)
        
        # 检查查询参数
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if self._check_malicious(value):
                return self._block_request(f"恶意查询参数: {key}")
        
        # 检查请求体（POST/PUT/PATCH）
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8", errors="ignore")
                    if self._check_malicious(body_str):
                        return self._block_request("恶意请求体")
            except:
                pass
        
        # 检查请求头
        for key, value in request.headers.items():
            if key.lower() in ["user-agent", "referer", "origin"]:
                if self._check_malicious(value):
                    return self._block_request(f"恶意请求头: {key}")
        
        return await call_next(request)
    
    def _check_malicious(self, value: str) -> bool:
        """检查是否包含恶意内容"""
        if not value:
            return False
        
        # SQL注入检查
        for pattern in self.SQL_INJECTION_RE:
            if pattern.search(value):
                return True
        
        # XSS检查
        for pattern in self.XSS_RE:
            if pattern.search(value):
                return True
        
        # 路径遍历检查
        for pattern in self.PATH_TRAVERSAL_RE:
            if pattern.search(value):
                return True
        
        # 命令注入检查
        for pattern in self.COMMAND_INJECTION_RE:
            if pattern.search(value):
                return True
        
        return False
    
    def _block_request(self, reason: str) -> Response:
        """阻止恶意请求"""
        return JSONResponse(
            status_code=403,
            content={
                "detail": "请求被安全策略阻止",
                "reason": reason,
                "code": "WAF_BLOCKED"
            }
        )


class IPBlacklistMiddleware(BaseHTTPMiddleware):
    """IP黑名单中间件"""
    
    def __init__(self, app, blacklist_file: str = None):
        super().__init__(app)
        self.blacklist = set()
        self.whitelist = set()
        
        if blacklist_file:
            self._load_blacklist(blacklist_file)
    
    def _load_blacklist(self, filepath: str):
        """从文件加载黑名单"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('#'):
                        self.blacklist.add(ip)
        except FileNotFoundError:
            pass
    
    def add_to_blacklist(self, ip: str):
        """添加IP到黑名单"""
        self.blacklist.add(ip)
    
    def remove_from_blacklist(self, ip: str):
        """从黑名单移除IP"""
        self.blacklist.discard(ip)
    
    def add_to_whitelist(self, ip: str):
        """添加IP到白名单"""
        self.whitelist.add(ip)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        
        # 白名单IP跳过检查
        if client_ip in self.whitelist:
            return await call_next(request)
        
        # 黑名单IP直接拒绝
        if client_ip in self.blacklist:
            return JSONResponse(
                status_code=403,
                content={"detail": "IP已被封禁"}
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip
        return request.client.host if request.client else "unknown"


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """请求大小限制中间件"""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):
        """
        初始化
        :param max_size: 最大请求体大小（字节），默认10MB
        """
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "请求体过大",
                    "max_size_mb": self.max_size / (1024 * 1024)
                }
            )
        
        return await call_next(request)


def setup_waf(app, enable_ip_blacklist: bool = True, max_request_size: int = 10 * 1024 * 1024):
    """配置WAF防火墙"""
    
    # 请求大小限制
    app.add_middleware(RequestSizeLimitMiddleware, max_size=max_request_size)
    
    # WAF规则检查
    app.add_middleware(WAFMiddleware)
    
    # IP黑名单（可选）
    if enable_ip_blacklist:
        app.add_middleware(IPBlacklistMiddleware)
    
    return app

# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
WAF防火墙规则配置
提供SQL注入、XSS、路径遍历等常见攻击防护
"""

import re

from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class WAFMiddleware(BaseHTTPMiddleware):
    """Web应用防火墙中间件"""
    # SQL注入特征
    # 注意:这些是 body/param 的特征;header 走更精简的 SQL_INJECTION_HEADER_PATTERNS
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|TRUNCATE|GRANT|REVOKE)\b\s+.*\b(FROM|INTO|TABLE|WHERE|SLEEP|BENCHMARK)\b)",
        r"(\bUNION\s+SELECT\b)",                # UNION SELECT (任意位置)
        r"(\b(OR|AND)\b\s+['\d].*?=\s*['\d])",   # OR 1=1 / AND '1'='1
        r"(0x[0-9a-f]{6,})",                      # hex-encoded payload
        r"(';\s*--(?!.*\b(end|else|fi)\b))",      # 注释注入 ' ; --
        r"(\bWAITFOR\s+DELAY\b|\bBENCHMARK\s*\()", # 时间盲注
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
    # 注意: 不在 body/param 中单独检测 | ; && 等管道/分隔符,
    # 因为合法密码中可能出现 P@ss|123 或 user;name。
    # 只检测: 操作符 + 命令名 (shell 注入的典型模式)
    COMMAND_INJECTION_PATTERNS = [
        r"(\|\s*(sh|bash|cmd|cat|rm|wget|curl|nc|python|perl|node|java|php|ruby|openssl)\b)",
        r"(;\s*(sh|bash|cmd|cat|rm|wget|curl|nc|python|perl|node|java|php|ruby|openssl)\b)",
        r"(&&\s*(sh|bash|cmd|cat|rm|wget|curl|nc|echo|chmod|mkdir|touch)\b)",
        r"(`[^`]+`)",                           # 反引号命令替换
        r"(\$\([^)]+\))",                        # $(command) 子shell
        r"(/bin/(sh|bash)\b)",                  # 直接调用 shell
        r"(cmd\.exe|powershell)",                # Windows 命令
    ]
    # 编译正则表达式
    SQL_INJECTION_RE = [re.compile(p, re.IGNORECASE)
                        for p in SQL_INJECTION_PATTERNS]
    XSS_RE = [re.compile(p, re.IGNORECASE) for p in XSS_PATTERNS]
    PATH_TRAVERSAL_RE = [re.compile(p, re.IGNORECASE)
                         for p in PATH_TRAVERSAL_PATTERNS]
    COMMAND_INJECTION_RE = [re.compile(p, re.IGNORECASE)
                            for p in COMMAND_INJECTION_PATTERNS]

    # === User-Agent 黑名单(P3-014) ===
    # 典型扫描器/爬虫/漏洞利用工具特征,即使通过其他向量仍应直接拒
    USER_AGENT_BLACKLIST_PATTERNS = [
        r"sqlmap",           # SQL 注入扫描器
        r"nikto",            # Web 漏洞扫描器
        r"nmap",             # 端口扫描
        r"masscan",          # 高速端口扫描
        r"zgrab",            # ZGrab 扫描器
        r"nessus",           # 漏洞扫描
        r"acunetix",         # Acunetix 扫描
        r"burpcollaborator", # Burp 协同服务器探测
        r"metasploit",       # 渗透框架
        r"w3af",             # Web 攻击审计框架
        r"dirbuster",        # 目录爆破
        r"gobuster",         # 目录爆破
        r"wfuzz",            # 模糊测试
        r"hydra",            # 暴力破解
        r"libwww-perl",      # 老旧 Perl 库,常被用于爬虫滥用
        r"python-requests/[0-9.]+",  # 裸 requests(可被业务网关允许,默认拦)
        r"go-http-client",   # 默认 Go 客户端(可被业务网关允许,默认拦)
        r"curl/[0-9.]+",     # 裸 curl
        r"wget/[0-9.]+",     # 裸 wget
    ]
    USER_AGENT_BLACKLIST_RE = [re.compile(p, re.IGNORECASE)
                               for p in USER_AGENT_BLACKLIST_PATTERNS]

    # === User-Agent 白名单豁免:API 内部调用 ===
    # 内部服务调用可设置 User-Agent: YouDingSaaS-Internal/1.0
    USER_AGENT_WHITELIST_PATTERNS = [
        r"YouDingSaaS-Internal",
        r"\bHealthChecker\b",    # 整词匹配,避免误匹配 "Health Check Service"
    ]
    USER_AGENT_WHITELIST_RE = [re.compile(p, re.IGNORECASE)
                               for p in USER_AGENT_WHITELIST_PATTERNS]

    # 允许设置 WAF_USER_AGENT_BYPASS=true 在极端场景(测试/迁移)跳过 UA 校验
    # 生产强烈不建议开启
    # 静态/文档路径 — 完全跳过 WAF(不接收 body)
    EXEMPT_PATH_PREFIXES = [
        # OpenAPI / Swagger 文档
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/openapi.json",   # 兼容自定义挂载
        "/api/docs",
        "/api/redoc",
        # 健康检查
        "/health",
        "/api/v1/health",
        # 登录注册(无 token 场景,需保证不被自身 WAF 拦)
        "/api/v1/system/login",
        "/api/v1/system/register",
        # 静态资源
        "/uploads",
        "/static",
    ]
    # 文件上传路径 — 不扫描 body（JPEG/PNG 二进制经 UTF-8 解码会误触 SQL/XSS 规则）
    UPLOAD_PATH_PREFIXES = [
        "/api/v1/files/upload",
        "/api/v1/content/pages/upload-image",
        "/api/v1/media-factory/upload",
        "/api/v1/cross-border/video-dub/upload",
    ]
    # 数据查询路径前缀 — 仍需扫描 body/query 中的 SQL/XSS/命令注入
    # 仅跳过 path_traversal 检查(避免业务路径含 .. 时误判)
    # 注意:仅使用无尾部斜杠的前缀,兼容 /api/v1/content 和 /api/v1/content/... 两种形式
    SCAN_BODY_PATH_PREFIXES = [
        "/api/v1/products",
        "/api/v1/content",       # 兼容 /api/v1/content 与 /api/v1/content/...
        "/api/v1/cases",
        "/api/v1/inquiries",
        "/api/v1/users",
        "/api/v1/system/audit",  # 无尾部斜杠
        "/api/v1/system/contact",
        "/api/v1/analytics",     # 无尾部斜杠
        "/api/v1/sitemap",
        "/api/v1/metrics",
        "/api/v1/performance",
        "/api/v1/seo",
    ]
    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        path = str(request.url.path)
        # 0) User-Agent 黑/白名单(P3-014)— 优先级最高,在所有路径策略之前
        ua_check = self._check_user_agent(request)
        if ua_check is not None:
            return ua_check

        # 1) 完全豁免:静态/文档/登录
        if any(path.startswith(prefix)
               for prefix in self.EXEMPT_PATH_PREFIXES):
            return await call_next(request)

        # 1.5) 文件上传 — 整请求跳过 WAF（JPEG/PNG 二进制经 UTF-8 解码会误触 SQL/XSS）
        if any(path.startswith(prefix)
               for prefix in self.UPLOAD_PATH_PREFIXES):
            return await call_next(request)

        # 2) 业务数据路径:扫描 body/query,但不扫 path 本身
        if any(path.startswith(prefix)
               for prefix in self.SCAN_BODY_PATH_PREFIXES):
            return await self._scan_body_and_params(request, call_next,
                                                    skip_path=True)

        # 3) 默认:全量扫描(包含 path/headers)
        return await self._scan_full(request, call_next)

    def _skip_waf_body(self, request: Request) -> bool:
        """multipart/文件上传 body 不做文本特征扫描，避免图片/视频二进制误拦。"""
        content_type = (request.headers.get("content-type") or "").lower()
        if "multipart/form-data" in content_type:
            return True
        path = str(request.url.path)
        return any(path.startswith(prefix) for prefix in self.UPLOAD_PATH_PREFIXES)

    async def _scan_body_and_params(self, request: Request, call_next,
                                    skip_path: bool = False):
        """_scan_body_and_params。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :param skip_path: 参数 skip_path
        :return: 返回处理结果。
        """
        # 检查查询参数
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if self._check_malicious(value, skip_path=skip_path):
                return self._block_request(f"恶意查询参数: {key}")

        # 检查请求体（POST/PUT/PATCH）
        if request.method in ["POST", "PUT", "PATCH"] and not self._skip_waf_body(request):
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8", errors="ignore")
                    if self._check_malicious(body_str, skip_path=skip_path):
                        return self._block_request("恶意请求体")
            except BaseException:
                pass

        return await call_next(request)

    async def _scan_full(self, request: Request, call_next):
        """_scan_full。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        # 路径扫描
        if self._check_malicious(str(request.url.path), skip_path=False):
            return self._block_request("恶意请求路径")

        # 查询参数
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if self._check_malicious(value, skip_path=False):
                return self._block_request(f"恶意查询参数: {key}")

        # 请求体
        if request.method in ["POST", "PUT", "PATCH"] and not self._skip_waf_body(request):
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8", errors="ignore")
                    if self._check_malicious(body_str, skip_path=False):
                        return self._block_request("恶意请求体")
            except BaseException:
                pass

        # 请求头
        # 注意:对 user-agent/referer/origin 这类客户端可自由构造的头,
        # 只跑 SQL/XSS 检查;不要跑命令注入/路径遍历(浏览器 UA 必然含 ; & ( ) $ 等)
        for key, value in request.headers.items():
            if key.lower() in ["user-agent", "referer", "origin"]:
                if self._check_header_malicious(value):
                    return self._block_request(f"恶意请求头: {key}")

        return await call_next(request)

    def _check_header_malicious(self, value: str) -> bool:
        """仅对请求头做精简的 SQL/XSS 检查(避免误拦合法浏览器 UA)

        浏览器 UA 必然含 ; ( ) 等"危险"字符,完整的 body 用 SQL 模式
        (含 -- ; 等) 对 header 太宽,会造成大面积误拦。
        这里只跑:
        - SQL 关键字(SELECT/UNION/DROP 等),需要 \\b 整词匹配
        - 完整 XSS 模式(这部分在 header 上相对安全)
        """
        if not value:
            return False
        for pattern in self.SQL_INJECTION_HEADER_RE:
            if pattern.search(value):
                return True
        for pattern in self.XSS_RE:
            if pattern.search(value):
                return True
        return False

    # === Header 专用 SQL 模式(只匹配整词关键字,不包含 -- ; 等会被 UA 误触的字符) ===
    SQL_INJECTION_HEADER_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|TRUNCATE|GRANT|REVOKE)\b\s+.*\b(FROM|INTO|TABLE|WHERE)\b)",
        r"(\b(OR|AND)\b\s+['\d].*?=\s*['\d])",   # OR 1=1 / AND '1'='1'
        r"(0x[0-9a-f]{6,})",                      # hex-encoded payload
    ]
    SQL_INJECTION_HEADER_RE = [re.compile(p, re.IGNORECASE)
                               for p in SQL_INJECTION_HEADER_PATTERNS]

    def _check_malicious(self, value: str, skip_path: bool = False) -> bool:
        """检查是否包含恶意内容
        :param value: 待检查字符串
        :param skip_path: True 时跳过路径遍历检查(用于业务 URL 含 ..)
        """
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

        # 路径遍历检查(可被业务路径场景跳过)
        if not skip_path:
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
                "code": "WAF_BLOCKED"})

    def _check_user_agent(self, request: Request) -> Optional[Response]:
        """User-Agent 黑/白名单校验(P3-014)

        1) 内部白名单(YouDingSaaS-Internal / HealthChecker)→ 放行
        2) 扫描器/漏洞工具特征 → 403 拦截
        3) 裸 HTTP 客户端(curl/wget/requests/go-http-client)→ 403 拦截
        4) 正常浏览器 UA → 放行
        5) 空 UA → 放行(很多合法 API 客户端不设置 UA,且前端 fetch 也会附 UA)
           但会记录到日志,后续可接入 IP 信誉库做二次判断

        Returns:
            None - 放行
            Response - 拦截响应
        """
        import os as _os
        if _os.environ.get("WAF_USER_AGENT_BYPASS", "").lower() in (
                "1", "true", "yes"):
            return None

        ua = request.headers.get("user-agent", "")
        # 白名单先于黑名单判断
        for pattern in self.USER_AGENT_WHITELIST_RE:
            if pattern.search(ua):
                return None

        # 黑名单
        for pattern in self.USER_AGENT_BLACKLIST_RE:
            if pattern.search(ua):
                return self._block_request(f"恶意 User-Agent: {ua[:60]}")

        return None


class IPBlacklistMiddleware(BaseHTTPMiddleware):
    """IP黑名单中间件"""
    def __init__(self, app, blacklist_file: str = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app: 参数 app
        :param blacklist_file: 参数 blacklist_file
        :return: 返回处理结果。
        """
        super().__init__(app)
        self.blacklist = set()
        self.whitelist = set()
        if blacklist_file:
            self._load_blacklist(blacklist_file)

    def _load_blacklist(self, filepath: str):
        """从文件加载黑名单"""
        try:
            with open(filepath, "r") as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith("#"):
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
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        client_ip = self._get_client_ip(request)
        # 白名单IP跳过检查
        if client_ip in self.whitelist:
            return await call_next(request)

        # 黑名单IP直接拒绝
        if client_ip in self.blacklist:
            return JSONResponse(status_code=403, content={"detail": "IP已被封禁"})

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
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(status_code=413, content={
                "detail": "请求体过大", "max_size_mb": self.max_size / (1024 * 1024)})

        return await call_next(request)


def setup_waf(app, enable_ip_blacklist: bool = True,
              max_request_size: int = 10 * 1024 * 1024):
    """配置WAF防火墙"""
    # 请求大小限制
    app.add_middleware(RequestSizeLimitMiddleware, max_size=max_request_size)
    # WAF规则检查
    app.add_middleware(WAFMiddleware)
    # IP黑名单（可选）
    if enable_ip_blacklist:
        app.add_middleware(IPBlacklistMiddleware)

    return app

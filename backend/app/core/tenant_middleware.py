"""
SaaS 租户中间件 - 从请求域名识别租户

工作流程:
  1. 提取 Host 头部 (如 customer1.youding-saas.com)
  2. 提取子域名前缀 (如 customer1)
  3. 查询该子域名对应的激活租户
  4. 将租户信息注入 request.state.tenant
  5. 为该请求设置租户作用域 (DB 过滤、日志上下文等)

域名模式:
  - customer1.youding-saas.com  -> 租户A 的独立站点
  - customer2.youding-saas.com  -> 租户B 的独立站点
  - www.youding-saas.com        -> 主站 (无租户)
  - youding-saas.com            -> 主站 (无租户)

TODO [P1/部署前]:
  - 在 DNS 配置 *.youding-saas.com 泛域名解析指向网关服务器
  - 在 nginx 配置 server_name *.youding-saas.com 统一收口到后端
  - ALLOWED_HOSTS 中添加泛域名 *.youding-saas.com
"""

import json
import logging
import re
import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.middleware_fastlane import is_probe_or_static

logger = logging.getLogger("tenant_middleware")

# 主站域名模式列表 —— 匹配这些时不触发租户路由
PRIMARY_DOMAIN_PATTERNS = [
    r"^(www\.)?youding-saas\.com$",
    r"^(www\.)?youding\.com$",
    r"^localhost(:\d+)?$",
    r"^127\.0\.0\.1(:\d+)?$",
]

# 编译缓存: cache_key -> (tenant_info | _CACHE_MISS, expire_at)
# 升级：L1 进程内带 TTL 缓存 + L2 Redis 分布式共享缓存（建议 1 落地）
_tenant_cache: dict[str, tuple[dict | object, float]] = {}
_CACHE_MISS = object()


def _get_redis_tenant_cache(cache_key: str) -> Optional[dict | object]:
    """尝试从 Redis L2 缓存读取租户数据。"""
    if not getattr(settings, "TENANT_CACHE_REDIS_ENABLED", True):
        return None
    try:
        from app.core.cache import redis_client
        if redis_client is None:
            return None
        raw = redis_client.get(f"tenant_cache:{cache_key}")
        if raw is None:
            return None
        if raw == "__MISS__":
            return _CACHE_MISS
        return json.loads(raw)
    except Exception as exc:
        logger.debug("Redis tenant cache get failed: %s", exc)
        return None


def _set_redis_tenant_cache(cache_key: str, data: dict | object, ttl_sec: int) -> None:
    """写入 Redis L2 分布式租户缓存。"""
    if not getattr(settings, "TENANT_CACHE_REDIS_ENABLED", True):
        return
    try:
        from app.core.cache import redis_client
        if redis_client is None:
            return
        val = "__MISS__" if data is _CACHE_MISS else json.dumps(data, ensure_ascii=False)
        redis_client.setex(f"tenant_cache:{cache_key}", ttl_sec, val)
    except Exception as exc:
        logger.debug("Redis tenant cache set failed: %s", exc)


def extract_subdomain(host: str) -> Optional[str]:
    """
    从 Host 中提取子域名前缀。

    示例:
      "customer1.youding-saas.com"  -> "customer1"
      "www.youding-saas.com"        -> None (主站)
      "youding-saas.com"            -> None (主站)
      "localhost:8000"              -> None (主站)
    """
    host = host.strip().lower()
    # 去除端口号
    host_no_port = re.sub(r":\d+$", "", host)
    # 检查是否是主站域名
    for pattern in PRIMARY_DOMAIN_PATTERNS:
        if re.match(pattern, host):
            return None
        if re.match(pattern, host_no_port):
            return None

    # 尝试提取子域名: xxx.youding-saas.com 或 xxx.youding.com
    # 也支持自定义域名: tenant.custom.com
    for suffix in ["youding-saas.com", "youding.com"]:
        if host_no_port.endswith(f".{suffix}"):
            sub = host_no_port[: -len(f".{suffix}")]
            if sub and "." not in sub:  # 仅单级子域名
                return sub

    # 非标准后缀的自定义域名 —— 直接尝试作为完整域名查询
    return host_no_port


class TenantMiddleware(BaseHTTPMiddleware):
    """
    SaaS 租户识别中间件。

    从请求域名提取子域名前缀，查询租户后注入 request.state.tenant。

    用法 (在 app/api/gateway.py 中注册):
        app.add_middleware(TenantMiddleware)
    """
    def __init__(self, app):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app: 参数 app
        :return: 返回处理结果。
        """
        super().__init__(app)
        # 延迟导入避免循环依赖
        from app.db.session import SessionLocal
        from app.models.tenant import Tenant
        self._SessionLocal = SessionLocal
        self._TenantModel = Tenant

    def _resolve_user_tenant_from_request(self, request) -> Optional[dict]:
        """ADR-002 T04 双通道：无子域名时从登录态解析用户所属租户（经 user_tenants）。

        平台级用户（super_admin/admin 或无 active 绑定）返回 None → 保持"看全部"。
        任何异常一律降级 None，绝不阻断请求（best-effort，与既有 Trace 注入同纪律）。
        """
        try:
            token = None
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                token = auth[7:].strip()
            if not token:
                from app.core.jwt_cookie import extract_token_from_cookie
                token = extract_token_from_cookie(request)
            if not token:
                return None
            from app.core.jwt_key_rotation import jwt_key_rotation_service
            payload = jwt_key_rotation_service.decode_token(token)
            if not payload:
                return None
            user_id = payload.get("sub")
            user_role = payload.get("role")
            if not user_id:
                return None
            if user_role in ("super_admin", "admin"):
                return None  # 平台级，跨租户
            from app.db.session import SessionLocal
            from app.models.user import User
            from app.models.tenant import UserTenant, Tenant
            db = SessionLocal()
            try:
                link = (
                    db.query(UserTenant)
                    .filter(UserTenant.user_id == str(user_id), UserTenant.is_active.is_(True))
                    .first()
                )
                if not link:
                    return None
                t = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
                if not t:
                    return None
                return {"id": str(t.id), "name": t.name}
            finally:
                db.close()
        except Exception:
            return None

    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        path = request.url.path
        if is_probe_or_static(path):
            return await call_next(request)

        host = request.headers.get("host", "")
        # ---------- 1. 提取子域名 ----------
        subdomain = extract_subdomain(host)
        logger.debug("TenantMiddleware: host=%s subdomain=%s", host, subdomain)
        # 主站 Admin/API（localhost、主域名）无租户上下文，跳过 DB
        if subdomain is None:
            # ADR-002 T04：双通道——无子域名时，尝试从登录态解析用户所属租户
            # （经 user_tenants 关联），注入 OTel 供事务级 SET LOCAL 使用；
            # 平台级用户（super_admin/admin/无绑定）解析为 None，保持"看全部"。
            user_tenant = self._resolve_user_tenant_from_request(request)
            request.state.tenant = user_tenant
            request.state.tenant_subdomain = None
            if user_tenant and user_tenant.get("id"):
                try:
                    from app.core.opentelemetry_config import set_tenant_span_attributes
                    set_tenant_span_attributes(
                        tenant_id=user_tenant["id"],
                        tenant_name=user_tenant.get("name", ""),
                    )
                except Exception:
                    pass
            return await call_next(request)

        # ---------- 2. 查询租户 ----------
        tenant_info = self._lookup_tenant(subdomain, host)
        # ---------- 3. 将租户信息注入 request.state ----------
        request.state.tenant = tenant_info
        request.state.tenant_subdomain = subdomain
        # ---------- 3.1 注入 Trace 租户属性 ----------
        if tenant_info:
            try:
                from app.core.opentelemetry_config import set_tenant_span_attributes
                set_tenant_span_attributes(
                    tenant_id=tenant_info.get("id", ""),
                    tenant_name=tenant_info.get("name", ""),
                )
            except Exception:
                pass  # Trace 注入失败不应阻塞请求

        # ---------- 4. 如果是租户域名但未找到匹配租户 -> 404 ----------
        if subdomain and not tenant_info:
            # 只有子域名明确指向租户域时才返回 404
            # 避免误拦截自定义域名
            if subdomain != host:  # 是标准子域名格式
                return JSONResponse(
                    status_code=404,
                    content={
                        "code": 404,
                        "message": "站点不存在或已停用",
                        "detail": f"未找到子域名 '{subdomain}' 对应的租户站点",
                    },
                )

        # ---------- 5. 继续处理请求 ----------
        response = await call_next(request)
        return response

    def _lookup_tenant(self, subdomain: str, full_host: str) -> Optional[dict]:
        """
        查询子域名对应的租户信息。

        优先从缓存读取，缓存 miss 则查数据库。
        首先尝试子域名匹配 tenant.domain，
        再尝试完整域名匹配 tenant.custom_domains JSON 数组。
        返回经过脱敏的租户公开信息字典。
        """
        host_clean = re.sub(r":\d+$", "", full_host.strip().lower())
        cache_key = f"{subdomain}|{host_clean}"
        now_ts = time.time()
        ttl = int(getattr(settings, "TENANT_CACHE_TTL_SEC", 60) or 60)

        # 1. 先查 L1 内存缓存（带 TTL）
        cached_entry = _tenant_cache.get(cache_key)
        if cached_entry:
            val, exp = cached_entry
            if now_ts < exp:
                return None if val is _CACHE_MISS else val
            else:
                _tenant_cache.pop(cache_key, None)

        # 2. 查 L2 Redis 分布式缓存
        l2_cached = _get_redis_tenant_cache(cache_key)
        if l2_cached is not None:
            _tenant_cache[cache_key] = (l2_cached, now_ts + ttl)
            return None if l2_cached is _CACHE_MISS else l2_cached

        # 3. 缓存均未命中，查询数据库
        try:
            db = self._SessionLocal()
            try:
                # ---- 1. 主域名匹配 ----
                tenant = (
                    db.query(self._TenantModel)
                    .filter(
                        self._TenantModel.domain == subdomain,
                        self._TenantModel.is_active,
                    )
                    .first()
                )
                # ---- 2. 完整 Host 匹配 tenant.domain（如 dev.local:8001） ----
                if not tenant and subdomain != host_clean:
                    tenant = (
                        db.query(self._TenantModel)
                        .filter(
                            self._TenantModel.domain == host_clean,
                            self._TenantModel.is_active,
                        )
                        .first()
                    )

                # ---- 3. custom_domains JSON 数组匹配（仅在前两步失败时） ----
                if not tenant:
                    tenant = self._lookup_by_custom_domain(db, full_host)

                if not tenant:
                    _tenant_cache[cache_key] = (_CACHE_MISS, now_ts + ttl)
                    _set_redis_tenant_cache(cache_key, _CACHE_MISS, ttl)
                    return None

                # 解析 settings JSON
                settings_dict = {}
                if tenant.settings:
                    try:
                        settings_dict = json.loads(tenant.settings)
                    except (json.JSONDecodeError, TypeError):
                        settings_dict = {}

                # 提取品牌信息
                brand = settings_dict.get("brand", {})
                white_label = settings_dict.get("white_label", {})
                tenant_info = {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "domain": tenant.domain,
                    "status": tenant.status,
                    "plan_code": tenant.plan.code if tenant.plan else None,
                    "brand": {
                        "site_title": brand.get("site_title", tenant.name),
                        "logo_url": brand.get("logo_url", white_label.get("logo_url", "")),
                        "brand_colors": brand.get("brand_colors", {
                            "primary": white_label.get("primary_color", "#1890ff"),
                            "secondary": "#6b7280",
                            "accent": "#f59e0b",
                        }),
                        "product_categories": brand.get("product_categories", []),
                        "company_name": brand.get("company_name", tenant.name),
                        "slogan": brand.get("slogan", ""),
                        "about_summary": brand.get("about_summary", ""),
                        "contact_phone": brand.get("contact_phone", tenant.contact_phone or ""),
                        "contact_email": brand.get("contact_email", tenant.contact_email or ""),
                        "footer_text": brand.get("footer_text", white_label.get("footer_text", "")),
                        "custom_css": brand.get("custom_css", white_label.get("custom_css", "")),
                    },
                }
                # 写入多级缓存（L1 进程内 TTL + L2 Redis 分布式）
                _tenant_cache[cache_key] = (tenant_info, now_ts + ttl)
                _set_redis_tenant_cache(cache_key, tenant_info, ttl)
                return tenant_info

            finally:
                db.close()

        except Exception as e:
            logger.error("TenantMiddleware: 查询租户失败 subdomain=%s error=%s", subdomain, str(e))
            return None

    def _lookup_by_custom_domain(self, db, full_host: str):
        """
        遍历所有激活租户，从 custom_domains JSON 数组中匹配完整域名。
        """
        full_host_clean = full_host.strip().lower()
        # 去除端口号
        full_host_clean = re.sub(r":\d+$", "", full_host_clean)
        all_tenants = (
            db.query(self._TenantModel)
            .filter(self._TenantModel.is_active)
            .all()
        )
        for t in all_tenants:
            if not t.custom_domains:
                continue
            try:
                domains = json.loads(t.custom_domains)
                if not isinstance(domains, list):
                    continue
                for d in domains:
                    if d.strip().lower() == full_host_clean:
                        return t
            except (json.JSONDecodeError, TypeError):
                continue
        return None

    @staticmethod
    def clear_cache():
        """清空租户缓存（当租户配置更新时调用）"""
        _tenant_cache.clear()


def get_current_tenant(request: Request) -> Optional[dict]:
    """
    快捷函数: 从 request.state 获取当前租户信息。

    用法:
        from app.core.tenant_middleware import get_current_tenant

        @router.get("/some-route")
        def handler(request: Request):
            tenant = get_current_tenant(request)
            if tenant:
                    logger.info("Current tenant: %s", tenant["name"])
    """
    return getattr(request.state, "tenant", None)


def is_tenant_request(request: Request) -> bool:
    """判断当前请求是否来自租户子域名"""
    return getattr(request.state, "tenant", None) is not None

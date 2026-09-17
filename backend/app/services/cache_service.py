# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""缓存服务 - 提供Redis缓存和响应缓存功能"""

import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.cache import redis_client as _shared_redis


class CacheService:
    """Redis缓存服务"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.redis_client = _shared_redis

    def _connect(self):
        """连接到Redis（统一使用 core/cache.py 的共享连接）"""
        self.redis_client = _shared_redis

    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get(key)
        except (redis.RedisError, Exception) as e:
            logger = logging.getLogger(__name__)
            logger.warning("Redis get 失败 key=%s: %s", key, e)
            return None

    def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """设置缓存值"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.set(key, value, ex=expire)
            return True
        except (redis.RedisError, Exception) as e:
            logger = logging.getLogger(__name__)
            logger.warning("Redis set 失败 key=%s: %s", key, e)
            return False

    def get_json(self, key: str) -> Optional[dict]:
        """获取JSON缓存"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(self, key: str, value: dict, expire: int = 3600) -> bool:
        """设置JSON缓存"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return self.set(key, json_str, expire)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("Redis set_json 失败 key=%s: %s", key, e)
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except (redis.RedisError, Exception) as e:
            logger = logging.getLogger(__name__)
            logger.warning("Redis delete 失败 key=%s: %s", key, e)
            return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.exists(key) > 0
        except (redis.RedisError, Exception) as e:
            logger = logging.getLogger(__name__)
            logger.warning("Redis exists 失败 key=%s: %s", key, e)
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存（使用 SCAN 避免 KEYS 阻塞生产 Redis）"""
        if not self.redis_client:
            return 0
        try:
            deleted = 0
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception:
            return 0

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """原子递增计数器"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.incr(key, amount)
        except Exception:
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.expire(key, seconds)
        except Exception:
            return False

    def pipeline(self):
        """获取管道对象用于批量操作"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.pipeline()
        except Exception:
            return None


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """响应缓存中间件"""
    CACHE_DURATION = {
        "GET": 300,  # 5分钟
        "HEAD": 300,
    }
    def __init__(self, app, cache_service: CacheService = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app: 参数 app
        :param cache_service: 参数 cache_service
        :return: 返回处理结果。
        """
        super().__init__(app)
        self.cache = cache_service or CacheService()

    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        # 只缓存GET请求
        if request.method not in self.CACHE_DURATION:
            return await call_next(request)

        # 构建缓存键
        cache_key = self._build_cache_key(request)
        # 检查缓存
        cached_response = self.cache.get_json(cache_key)
        if cached_response:
            response = Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
            )
            response.headers["X-Cache"] = "HIT"
            return response

        # 执行请求
        response = await call_next(request)
        # 缓存成功的响应
        if response.status_code == 200:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            cache_data = {
                "content": body.decode("utf-8"),
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }
            self.cache.set_json(cache_key, cache_data,
                                self.CACHE_DURATION[request.method])

            # 重建响应
            response = Response(
                content=cache_data["content"],
                status_code=cache_data["status_code"],
                headers=cache_data["headers"])

        response.headers["X-Cache"] = "MISS"
        return response

    def _build_cache_key(self, request: Request) -> str:
        """构建缓存键"""
        return f"cache:{request.method}:{request.url.path}:{hash(frozenset(request.query_params.items()))}"


def cached(expire: int = 3600):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """wrapper。

            参数说明：
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            cache_service = CacheService()
            # 构建缓存键
            key_parts = [func.__name__]
            for arg in args:
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            cache_key = ":".join(key_parts)
            # 检查缓存
            cached_result = cache_service.get_json(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = func(*args, **kwargs)
            # 缓存结果
            cache_service.set_json(cache_key, result, expire)
            return result

        return wrapper

    return decorator


# 全局缓存实例
cache_service = CacheService()

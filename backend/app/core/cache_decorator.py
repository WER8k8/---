import functools
import hashlib
import json
import logging
from typing import Any, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.cache import redis_client as _shared_redis

logger = logging.getLogger(__name__)


def get_redis_client():
    """获取共享 Redis 连接（统一使用 core/cache.py 的连接）"""
    return _shared_redis if _shared_redis else None


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """generate_cache_key。

    参数说明：
    :param prefix: 参数 prefix
    :param *args: 参数 *args
    :param **kwargs: 参数 **kwargs
    :return: 返回处理结果。
    """
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"


def cache_response(expire: int = 300, prefix: str = "api"):
    """cache_response。

    参数说明：
    :param expire: 参数 expire
    :param prefix: 参数 prefix
    :return: 返回处理结果。
    """
    def decorator(func):
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """wrapper。

            参数说明：
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                return await func(*args, **kwargs)

            cache_key = generate_cache_key(
                prefix, request.url.path, dict(
                    request.query_params))

            try:
                redis_client = get_redis_client()
                if redis_client:
                    cached = redis_client.get(cache_key)
                    if cached:
                        logger.debug(f"Cache hit: {cache_key}")
                        cached_data = json.loads(cached)
                        return JSONResponse(content=cached_data)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

            result = await func(*args, **kwargs)
            if hasattr(result, "body"):
                try:
                    body_bytes = result.body
                    if isinstance(body_bytes, bytes):
                        body_str = body_bytes.decode("utf-8")
                        body_data = json.loads(body_str)
                        try:
                            redis_client = get_redis_client()
                            if redis_client:
                                redis_client.setex(
                                    cache_key, expire, json.dumps(
                                        body_data, ensure_ascii=False))
                                logger.debug(
                                    f"Cache set: {cache_key}, expire: {expire}s")
                        except Exception as e:
                            logger.warning(f"Redis cache write failed: {e}")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """invalidate_cache。

    参数说明：
    :param pattern: 参数 pattern
    :return: 返回处理结果。
    """
    def decorator(func):
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """wrapper。

            参数说明：
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            result = await func(*args, **kwargs)
            try:
                redis_client = get_redis_client()
                if redis_client:
                    keys = list(redis_client.scan_iter(match=f"cache:{pattern}*", count=100))
                    if keys:
                        redis_client.delete(*keys)
                        logger.info(
                            f"Cache invalidated: {pattern}, count: {len(keys)}")
            except Exception as e:
                logger.warning(f"Redis cache invalidation failed: {e}")

            return result

        return wrapper

    return decorator


def get_cache_stats() -> dict:
    """get_cache_stats。
    :return: 返回处理结果。
    """
    try:
        redis_client = get_redis_client()
        if redis_client:
            keys = list(redis_client.scan_iter(match="cache:*", count=100))
            return {"total_keys": len(keys), "status": "connected"}
    except Exception as e:
        logger.warning(f"Cache stats failed: {e}")

    return {"total_keys": 0, "status": "disconnected"}

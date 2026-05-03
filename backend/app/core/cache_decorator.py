import functools
import hashlib
import json
from typing import Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None
    return _redis_client


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"


def cache_response(expire: int = 300, prefix: str = "api"):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                return await func(*args, **kwargs)
            
            cache_key = generate_cache_key(prefix, request.url.path, dict(request.query_params))
            
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
                                    cache_key,
                                    expire,
                                    json.dumps(body_data, ensure_ascii=False)
                                )
                                logger.debug(f"Cache set: {cache_key}, expire: {expire}s")
                        except Exception as e:
                            logger.warning(f"Redis cache write failed: {e}")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            try:
                redis_client = get_redis_client()
                if redis_client:
                    keys = redis_client.keys(f"cache:{pattern}*")
                    if keys:
                        redis_client.delete(*keys)
                        logger.info(f"Cache invalidated: {pattern}, count: {len(keys)}")
            except Exception as e:
                logger.warning(f"Redis cache invalidation failed: {e}")
            
            return result
        return wrapper
    return decorator


def get_cache_stats() -> dict:
    try:
        redis_client = get_redis_client()
        if redis_client:
            keys = redis_client.keys("cache:*")
            return {
                "total_keys": len(keys),
                "status": "connected"
            }
    except Exception as e:
        logger.warning(f"Cache stats failed: {e}")
    
    return {"total_keys": 0, "status": "disconnected"}

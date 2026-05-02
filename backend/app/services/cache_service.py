"""缓存服务 - 提供Redis缓存和响应缓存功能"""

import json
import time
from typing import Any, Optional, Callable
from functools import wraps

import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class CacheService:
    """Redis缓存服务"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """连接到Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # 测试连接
            self.redis_client.ping()
        except Exception:
            self.redis_client = None
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get(key)
        except Exception:
            return None
    
    def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """设置缓存值"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.set(key, value, ex=expire)
            return True
        except Exception:
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
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.exists(key) > 0
        except Exception:
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存"""
        if not self.redis_client:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception:
            return 0


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """响应缓存中间件"""
    
    CACHE_DURATION = {
        'GET': 300,  # 5分钟
        'HEAD': 300,
    }
    
    def __init__(self, app, cache_service: CacheService = None):
        super().__init__(app)
        self.cache = cache_service or CacheService()
    
    async def dispatch(self, request: Request, call_next):
        # 只缓存GET请求
        if request.method not in self.CACHE_DURATION:
            return await call_next(request)
        
        # 构建缓存键
        cache_key = self._build_cache_key(request)
        
        # 检查缓存
        cached_response = self.cache.get_json(cache_key)
        if cached_response:
            response = Response(
                content=cached_response['content'],
                status_code=cached_response['status_code'],
                headers=cached_response['headers']
            )
            response.headers['X-Cache'] = 'HIT'
            return response
        
        # 执行请求
        response = await call_next(request)
        
        # 缓存成功的响应
        if response.status_code == 200:
            body = b''
            async for chunk in response.body_iterator:
                body += chunk
            
            cache_data = {
                'content': body.decode('utf-8'),
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
            
            self.cache.set_json(cache_key, cache_data, self.CACHE_DURATION[request.method])
            
            # 重建响应
            response = Response(
                content=cache_data['content'],
                status_code=cache_data['status_code'],
                headers=cache_data['headers']
            )
        
        response.headers['X-Cache'] = 'MISS'
        return response
    
    def _build_cache_key(self, request: Request) -> str:
        """构建缓存键"""
        return f"cache:{request.method}:{request.url.path}:{hash(frozenset(request.query_params.items()))}"


def cached(expire: int = 3600):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
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

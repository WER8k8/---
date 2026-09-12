import asyncio
import functools
import logging
import random
from typing import Callable, Any

from app.core.circuit_breaker import CircuitBreakerRegistry

logger = logging.getLogger(__name__)

def with_retry(
    max_retries: int = 3,
    backoff: str = 'exponential',
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (Exception,)
):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except retryable_exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Retry limit reached for {func.__name__} after {max_retries} attempts.")
                        raise
                    
                    if backoff == 'exponential':
                        delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    else:
                        delay = base_delay
                    
                    # Add jitter
                    delay = delay * (0.5 + random.random())
                    
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {delay:.2f}s due to {type(e).__name__}: {e}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


def with_timeout(seconds: float):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            else:
                loop = asyncio.get_running_loop()
                return await asyncio.wait_for(loop.run_in_executor(None, lambda: func(*args, **kwargs)), timeout=seconds)
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback triggered for {func.__name__} due to {type(e).__name__}: {e}")
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)
        return wrapper
    return decorator


def with_circuit_breaker(name: str, **breaker_kwargs):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = await CircuitBreakerRegistry.get_or_create(name, **breaker_kwargs)
            
            async def _inner_func(*_args, **_kwargs):
                if asyncio.iscoroutinefunction(func):
                    return await func(*_args, **_kwargs)
                else:
                    return func(*_args, **_kwargs)
                    
            return await breaker.call(_inner_func, *args, **kwargs)
        return wrapper
    return decorator


def resilient(breaker_name: str, timeout_sec: float, max_retries: int, fallback_func: Callable):
    def decorator(func: Callable):
        @functools.wraps(func)
        @with_fallback(fallback_func)
        @with_retry(max_retries=max_retries)
        @with_circuit_breaker(name=breaker_name)
        @with_timeout(seconds=timeout_sec)
        async def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

import asyncio
import time
import unittest
from unittest.mock import Mock

from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerRegistry
)
from app.core.resilience import (
    with_retry,
    with_timeout,
    with_fallback,
    with_circuit_breaker,
    resilient
)

class TestCircuitBreaker(unittest.IsolatedAsyncioTestCase):
    
    async def test_circuit_breaker_stays_closed_on_success(self):
        cb = CircuitBreaker("test_cb_success", failure_threshold=2)
        
        async def success_func():
            return "ok"
            
        res = await cb.call(success_func)
        self.assertEqual(res, "ok")
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failure_count, 0)
        
    async def test_circuit_breaker_opens_on_failures(self):
        cb = CircuitBreaker("test_cb_fail", failure_threshold=2)
        
        async def fail_func():
            raise ValueError("fail")
            
        with self.assertRaises(ValueError):
            await cb.call(fail_func)
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failure_count, 1)
        
        with self.assertRaises(ValueError):
            await cb.call(fail_func)
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertEqual(cb.failure_count, 2)
        
    async def test_circuit_breaker_rejects_when_open(self):
        cb = CircuitBreaker("test_cb_open", failure_threshold=1, recovery_timeout_sec=5.0)
        
        async def fail_func():
            raise ValueError("fail")
            
        with self.assertRaises(ValueError):
            await cb.call(fail_func)
            
        self.assertEqual(cb.state, CircuitState.OPEN)
        
        async def success_func():
            return "ok"
            
        with self.assertRaises(CircuitOpenError):
            await cb.call(success_func)
            
    async def test_circuit_breaker_half_open_recovery(self):
        cb = CircuitBreaker("test_cb_half_open_recv", failure_threshold=1, recovery_timeout_sec=0.1, success_threshold=2)
        
        async def fail_func():
            raise ValueError("fail")
            
        with self.assertRaises(ValueError):
            await cb.call(fail_func)
            
        self.assertEqual(cb.state, CircuitState.OPEN)
        
        await asyncio.sleep(0.15)
        
        async def success_func():
            return "ok"
            
        res1 = await cb.call(success_func)
        self.assertEqual(res1, "ok")
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        
        res2 = await cb.call(success_func)
        self.assertEqual(res2, "ok")
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failure_count, 0)

    async def test_circuit_breaker_half_open_failure(self):
        cb = CircuitBreaker("test_cb_half_open_fail", failure_threshold=1, recovery_timeout_sec=0.1)
        
        async def fail_func():
            raise ValueError("fail")
            
        with self.assertRaises(ValueError):
            await cb.call(fail_func)
            
        self.assertEqual(cb.state, CircuitState.OPEN)
        
        await asyncio.sleep(0.15)
        
        with self.assertRaises(ValueError):
            await cb.call(fail_func)
            
        self.assertEqual(cb.state, CircuitState.OPEN)

    async def test_retry_decorator(self):
        attempts = 0
        
        @with_retry(max_retries=2, base_delay=0.1, max_delay=0.2)
        async def flaky_func():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("temporary error")
            return "success"
            
        res = await flaky_func()
        self.assertEqual(res, "success")
        self.assertEqual(attempts, 3)
        
    async def test_timeout_decorator(self):
        @with_timeout(seconds=0.1)
        async def slow_func():
            await asyncio.sleep(0.3)
            return "done"
            
        with self.assertRaises(asyncio.TimeoutError):
            await slow_func()
            
    async def test_fallback_decorator(self):
        async def fallback():
            return "fallback"
            
        @with_fallback(fallback_func=fallback)
        async def fail_func():
            raise RuntimeError("error")
            
        res = await fail_func()
        self.assertEqual(res, "fallback")
        
    async def test_registry_singleton(self):
        cb1 = await CircuitBreakerRegistry.get_or_create("singleton_test", failure_threshold=1)
        cb2 = await CircuitBreakerRegistry.get_or_create("singleton_test")
        
        self.assertIs(cb1, cb2)
        
        status = await CircuitBreakerRegistry.get_all_status()
        self.assertIn("singleton_test", status)
        
        await CircuitBreakerRegistry.reset("singleton_test")
        cb3 = await CircuitBreakerRegistry.get_or_create("singleton_test")
        self.assertIsNot(cb1, cb3)

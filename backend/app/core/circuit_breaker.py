import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Gauge, Counter
    cb_state = Gauge('circuit_breaker_state', 'Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)', ['name'])
    cb_failures = Counter('circuit_breaker_failures_total', 'Circuit breaker total failures', ['name'])
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class CircuitState(Enum):
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


class CircuitBreakerError(Exception):
    """Base class for Circuit Breaker exceptions"""
    pass


class CircuitOpenError(CircuitBreakerError):
    """Raised when the circuit is open"""
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = 0.0
        self._lock = asyncio.Lock()
        
        self._update_metrics()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def last_failure_time(self) -> float:
        return self._last_failure_time

    def _update_metrics(self):
        if PROMETHEUS_AVAILABLE:
            cb_state.labels(name=self.name).set(self._state.value)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.recovery_timeout_sec:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                    logger.info(f"CircuitBreaker {self.name} transitioned to HALF_OPEN")
                    self._update_metrics()
                else:
                    raise CircuitOpenError(f"CircuitBreaker {self.name} is OPEN")

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(f"CircuitBreaker {self.name} is HALF_OPEN and max calls reached")
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._success_count += 1
                    if self._success_count >= self.success_threshold:
                        self._state = CircuitState.CLOSED
                        self._failure_count = 0
                        logger.info(f"CircuitBreaker {self.name} recovered and transitioned to CLOSED")
                        self._update_metrics()
                elif self._state == CircuitState.CLOSED:
                    self._failure_count = 0
            return result
        except Exception as e:
            if isinstance(e, CircuitOpenError):
                raise
            
            async with self._lock:
                self._last_failure_time = time.time()
                if PROMETHEUS_AVAILABLE:
                    cb_failures.labels(name=self.name).inc()

                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.OPEN
                    logger.warning(f"CircuitBreaker {self.name} failed in HALF_OPEN, returning to OPEN")
                    self._update_metrics()
                elif self._state == CircuitState.CLOSED:
                    self._failure_count += 1
                    if self._failure_count >= self.failure_threshold:
                        self._state = CircuitState.OPEN
                        logger.warning(f"CircuitBreaker {self.name} exceeded failure threshold, transitioning to OPEN")
                        self._update_metrics()
            raise


class CircuitBreakerRegistry:
    _instance = None
    _lock = asyncio.Lock()
    _breakers: Dict[str, CircuitBreaker] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CircuitBreakerRegistry, cls).__new__(cls)
            cls._instance._breakers = {}
        return cls._instance

    @classmethod
    async def get_or_create(cls, name: str, **kwargs) -> CircuitBreaker:
        async with cls._lock:
            if name not in cls._instance._breakers:
                cls._instance._breakers[name] = CircuitBreaker(name=name, **kwargs)
            return cls._instance._breakers[name]

    @classmethod
    async def get_all_status(cls) -> Dict[str, str]:
        async with cls._lock:
            return {
                name: breaker.state.name
                for name, breaker in cls._instance._breakers.items()
            }

    @classmethod
    async def reset(cls, name: str):
        async with cls._lock:
            if name in cls._instance._breakers:
                kwargs = {
                    "failure_threshold": cls._instance._breakers[name].failure_threshold,
                    "recovery_timeout_sec": cls._instance._breakers[name].recovery_timeout_sec,
                    "half_open_max_calls": cls._instance._breakers[name].half_open_max_calls,
                    "success_threshold": cls._instance._breakers[name].success_threshold,
                }
                cls._instance._breakers[name] = CircuitBreaker(name=name, **kwargs)

# Initialize singleton
CircuitBreakerRegistry()

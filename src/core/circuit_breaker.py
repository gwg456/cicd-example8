"""
Circuit breaker pattern implementation for fault tolerance
"""
import asyncio
import functools
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional, Union

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    
    The circuit breaker pattern prevents cascading failures by
    temporarily blocking requests to a failing service.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected
    - HALF_OPEN: Testing if service has recovered
    
    Example:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=ConnectionError
        )
        
        @breaker
        def call_external_service():
            # Function that might fail
            pass
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        success_threshold: int = 2,
        name: Optional[str] = None,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
            success_threshold: Successes needed to close circuit from half-open
            name: Name for this circuit breaker
            on_open: Callback when circuit opens
            on_close: Callback when circuit closes
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.name = name or "CircuitBreaker"
        self.on_open = on_open
        self.on_close = on_close
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = threading.RLock()
        
        # Metrics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._circuit_open_count = 0
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)"""
        return self.state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)"""
        return self.state == CircuitState.HALF_OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        with self._lock:
            if self._state != CircuitState.OPEN:
                return False
            
            if self._last_failure_time is None:
                return False
            
            return (
                datetime.now() - self._last_failure_time
            ).total_seconds() >= self.recovery_timeout
    
    def _record_success(self):
        """Record a successful call"""
        with self._lock:
            self._total_successes += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._close_circuit()
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    def _record_failure(self):
        """Record a failed call"""
        with self._lock:
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                self._open_circuit()
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        with self._lock:
            if self._state != CircuitState.OPEN:
                self._state = CircuitState.OPEN
                self._circuit_open_count += 1
                logger.warning(
                    f"Circuit breaker '{self.name}' opened after {self._failure_count} failures"
                )
                
                if self.on_open:
                    try:
                        self.on_open()
                    except Exception as e:
                        logger.error(f"Error in on_open callback: {e}")
    
    def _close_circuit(self):
        """Close the circuit"""
        with self._lock:
            if self._state != CircuitState.CLOSED:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                logger.info(f"Circuit breaker '{self.name}' closed")
                
                if self.on_close:
                    try:
                        self.on_close()
                    except Exception as e:
                        logger.error(f"Error in on_close callback: {e}")
    
    def _half_open_circuit(self):
        """Set circuit to half-open state"""
        with self._lock:
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0
            logger.info(f"Circuit breaker '{self.name}' half-open, testing recovery")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function through the circuit breaker
        
        Args:
            func: Function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function fails
        """
        with self._lock:
            self._total_calls += 1
            
            # Check if we should attempt reset
            if self._should_attempt_reset():
                self._half_open_circuit()
            
            # Reject if circuit is open
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open"
                )
        
        # Attempt the call
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call an async function through the circuit breaker
        
        Args:
            func: Async function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function fails
        """
        with self._lock:
            self._total_calls += 1
            
            # Check if we should attempt reset
            if self._should_attempt_reset():
                self._half_open_circuit()
            
            # Reject if circuit is open
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open"
                )
        
        # Attempt the call
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator usage of circuit breaker
        
        Args:
            func: Function to wrap
        
        Returns:
            Wrapped function
        """
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.async_call(func, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self.call(func, *args, **kwargs)
            return wrapper
    
    def reset(self):
        """Manually reset the circuit breaker"""
        with self._lock:
            self._close_circuit()
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
    
    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""
        with self._lock:
            success_rate = (
                self._total_successes / self._total_calls * 100
                if self._total_calls > 0
                else 0
            )
            
            return {
                "name": self.name,
                "state": self._state.value,
                "total_calls": self._total_calls,
                "total_successes": self._total_successes,
                "total_failures": self._total_failures,
                "success_rate": round(success_rate, 2),
                "failure_count": self._failure_count,
                "circuit_open_count": self._circuit_open_count,
                "last_failure_time": (
                    self._last_failure_time.isoformat()
                    if self._last_failure_time
                    else None
                ),
            }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception,
    success_threshold: int = 2,
    name: Optional[str] = None,
) -> Callable:
    """
    Decorator factory for circuit breaker
    
    Args:
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds before attempting recovery
        expected_exception: Exception type to catch
        success_threshold: Successes needed to close from half-open
        name: Circuit breaker name
    
    Returns:
        Decorator function
    
    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        def risky_operation():
            # Operation that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            success_threshold=success_threshold,
            name=name or func.__name__,
        )
        return breaker(func)
    
    return decorator


# Global circuit breaker registry
_circuit_breakers = {}


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get a circuit breaker by name"""
    return _circuit_breakers.get(name)


def register_circuit_breaker(breaker: CircuitBreaker):
    """Register a circuit breaker globally"""
    _circuit_breakers[breaker.name] = breaker


def get_all_circuit_breakers() -> dict:
    """Get all registered circuit breakers"""
    return _circuit_breakers.copy()


def reset_all_circuit_breakers():
    """Reset all registered circuit breakers"""
    for breaker in _circuit_breakers.values():
        breaker.reset()
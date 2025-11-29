"""
Timeout and Retry Utilities
Enterprise-grade timeout handling with retry logic and circuit breakers
"""

import asyncio
import logging
import time
from typing import Callable, Any, Optional, TypeVar, Awaitable
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TimeoutError(Exception):
    """Custom timeout error with context."""
    def __init__(self, message: str, operation: str, timeout: float):
        super().__init__(message)
        self.operation = operation
        self.timeout = timeout


class CircuitBreakerError(Exception):
    """Circuit breaker is open - too many failures."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False
    
    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"[CIRCUIT_BREAKER] Circuit opened after {self.failure_count} failures")
    
    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if self.last_failure_time and (time.time() - self.last_failure_time) >= self.recovery_timeout:
            logger.info("[CIRCUIT_BREAKER] Attempting recovery - half-open state")
            self.is_open = False
            self.failure_count = 0
            return True
        
        return False
    
    def get_state(self) -> dict:
        """Get circuit breaker state for monitoring."""
        return {
            "is_open": self.is_open,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "can_attempt": self.can_attempt()
        }


# Global circuit breakers for different operations
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(operation: str) -> CircuitBreaker:
    """Get or create circuit breaker for an operation."""
    if operation not in _circuit_breakers:
        _circuit_breakers[operation] = CircuitBreaker()
    return _circuit_breakers[operation]


async def with_timeout(
    coro: Awaitable[T],
    timeout: float,
    operation: str = "operation",
    default: Optional[T] = None,
    on_timeout: Optional[Callable[[], T]] = None
) -> T:
    """
    Execute coroutine with timeout and fallback.
    
    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        operation: Operation name for logging
        default: Default value to return on timeout
        on_timeout: Callback to execute on timeout (returns value)
    
    Returns:
        Result of coroutine or fallback value
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.warning(f"[TIMEOUT] {operation} timed out after {timeout}s")
        if on_timeout:
            return on_timeout()
        if default is not None:
            return default
        raise TimeoutError(f"{operation} timed out after {timeout}s", operation, timeout)


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    circuit_breaker: Optional[CircuitBreaker] = None
):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        circuit_breaker: Optional circuit breaker instance
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if circuit_breaker and not circuit_breaker.can_attempt():
                raise CircuitBreakerError(f"Circuit breaker is open for {func.__name__}")
            
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"[RETRY] {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        if circuit_breaker:
                            circuit_breaker.record_failure()
                        logger.error(f"[RETRY] {func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        return wrapper
    return decorator


async def safe_execute(
    coro: Awaitable[T],
    operation: str,
    timeout: float = 30.0,
    default: Optional[T] = None,
    on_error: Optional[Callable[[Exception], T]] = None,
    circuit_breaker: Optional[CircuitBreaker] = None
) -> T:
    """
    Safely execute a coroutine with timeout, retry, and error handling.
    
    Args:
        coro: Coroutine to execute
        operation: Operation name for logging
        timeout: Timeout in seconds
        default: Default value on timeout/error
        on_error: Error handler callback
        circuit_breaker: Optional circuit breaker
    
    Returns:
        Result or fallback value
    """
    if circuit_breaker and not circuit_breaker.can_attempt():
        logger.warning(f"[SAFE_EXECUTE] Circuit breaker open for {operation}")
        if default is not None:
            return default
        raise CircuitBreakerError(f"Circuit breaker is open for {operation}")
    
    try:
        result = await with_timeout(coro, timeout, operation, default)
        if circuit_breaker:
            circuit_breaker.record_success()
        return result
    except Exception as e:
        logger.error(f"[SAFE_EXECUTE] {operation} failed: {str(e)}", exc_info=True)
        if circuit_breaker:
            circuit_breaker.record_failure()
        if on_error:
            return on_error(e)
        if default is not None:
            return default
        raise


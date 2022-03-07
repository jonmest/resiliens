#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

from datetime import timedelta, datetime
from functools import wraps
from inspect import isgeneratorfunction
from math import ceil, floor
from time import monotonic
from types import TracebackType
from typing import Union, Callable, Optional, Type, Any

from src.resiliens.circuit_breaker.CircuitBreakerException import CircuitBreakerException
from src.resiliens.circuit_breaker.SlidingWindow import SlidingWindow
from src.resiliens.circuit_breaker.manager.CircuitBreakerManager import CircuitBreakerManager
from src.resiliens.circuit_breaker.CircuitBreakerState import CircuitBreakerState
from src.resiliens.circuit_breaker.CircuitBreakerStatus import CircuitBreakerStatus


class CircuitBreakerClass:
    _max_attempts: int
    _reset_timeout: Union[float, int]
    _expected_exception: Type[BaseException]
    _fallback_function: Callable
    _fallback_function_with_exception: Callable
    _sliding_window: SlidingWindow

    def __init__(self,
                 max_attempts: int = 5,
                 reset_timeout: Union[float, int] = 20_000,
                 sliding_window_length: int = None,
                 expected_exception: Type[BaseException] = Exception,
                 name: str = None,
                 fallback_function: Callable = None,
                 fallback_function_with_exception: Callable = None):
        """

        :param max_attempts: Max failed attempts until the circuit breaker should be opened
        :param reset_timeout:
        Number of milliseconds until an opened circuit breaker should become half-opened and allow new attempts
        :param expected_exception: The
        exception the circuit breaker should expect as a failure (e.g. ConnectionError, RequestException)
        :param
        name: Name of the circuit breaker instance. Mostly useful if you intend to use the CircuitBreakerManager.
        :param fallback_function: A function to use as fallback if the circuit breaker is opened.
        :param fallback_function_with_exception: A function to use as fallback if the circuit breaker is opened.
        The first argument supplied to it will be the most recent exception (i.e.
        fallback_function_with_exception(last_exception, *args, **kwargs))
        """

        self._state = CircuitBreakerState(status=CircuitBreakerStatus.CLOSED,
                                          fail_count=0,
                                          last_failure=None,
                                          opened=monotonic())
        self._max_attempts = max_attempts
        self._reset_timeout = reset_timeout / 1000  # From milliseconds to seconds
        self._expected_exception = expected_exception
        self._fallback_function = fallback_function
        self._fallback_function_with_exception = fallback_function_with_exception
        self._name = name
        if sliding_window_length:
            self._sliding_window = SlidingWindow(sliding_window_length)

    @property
    def status(self):
        if self._state.status == CircuitBreakerStatus.OPEN and self.open_seconds_remaining <= 0:
            return CircuitBreakerStatus.HALF_OPEN
        return self._state.status

    @property
    def max_attempts(self):
        return self._max_attempts

    @property
    def open_until(self):
        return datetime.utcnow() + timedelta(
            seconds=self.open_seconds_remaining)

    @property
    def open_seconds_remaining(self) -> int:
        remain = (self._state.opened + self._reset_timeout) - monotonic()

        return ceil(remain) if remain > 0 else floor(remain)

    @property
    def failure_count(self):
        return self._state.fail_count

    @property
    def closed(self):
        return self.status == CircuitBreakerStatus.CLOSED

    @property
    def opened(self):
        return self.status == CircuitBreakerStatus.OPEN

    @property
    def name(self):
        return self._name

    @property
    def last_failure(self):
        return self._state.last_failure

    @property
    def fallback_function(self):
        if self._fallback_function is not None:
            return self._fallback_function
        return self._fallback_function_with_exception

    def __call__(self, decorated_function):
        return self.decorate(decorated_function)

    def __enter__(self):
        return None

    def __exit__(self, exception_type: Optional[Type[BaseException]],
                 exception_value: Optional[BaseException],
                 exception_traceback: Optional[TracebackType]) -> bool:
        if exception_type and issubclass(exception_type,
                                         self._expected_exception):
            self._state.last_failure = exception_value
            self.__call_failed()
        else:
            self.__call_succeeded()
        return False

    def decorate(self, function_to_decorate) -> Callable:
        if self._name is None:
            self._name = function_to_decorate.__name__

        CircuitBreakerManager.register(self)

        if isgeneratorfunction(function_to_decorate):
            call = self.call_generator
        else:
            call = self.call

        @wraps(function_to_decorate)
        def wrapper(*args, **kwargs):
            if self.opened:
                if self.fallback_function:
                    return self.fallback_function(*args, **kwargs)
                elif self._fallback_function_with_exception:
                    return self._fallback_function_with_exception(
                        self._state.last_failure, *args, **kwargs)
                raise CircuitBreakerException(self)
            return call(function_to_decorate, *args, **kwargs)

        return wrapper

    def call(self, func, *args, **kwargs) -> Any:
        with self:
            return func(*args, **kwargs)

    def call_generator(self, func, *args, **kwargs):
        with self:
            for el in func(*args, **kwargs):
                yield el

    def __call_succeeded(self) -> None:
        self._state.status = CircuitBreakerStatus.CLOSED
        self._state.last_failure = None
        self._state.fail_count = 0
        if self._sliding_window:
            self._sliding_window.add(True)

    def __call_failed(self) -> None:
        self._state.fail_count += 1
        if self._sliding_window:
            self._sliding_window.add(False)
            if self._sliding_window.get_failure_count() >= self._max_attempts:
                self._state.status = CircuitBreakerStatus.OPEN
                self._state.opened = monotonic()
        elif self._state.fail_count >= self._max_attempts:
            self._state.status = CircuitBreakerStatus.OPEN
            self._state.opened = monotonic()

    def force_open(self) -> None:
        self._state.status = CircuitBreakerStatus.OPEN
        self._state.opened = monotonic()

    def force_reset(self) -> None:
        self.__call_succeeded()

    def __str__(self, *args, **kwargs) -> str:
        return self._name


def CircuitBreaker(max_attempts: int = 5,
                   reset_timeout: Union[float, int] = 20_000,
                   sliding_window_length: int = None,
                   expected_exception: Type[BaseException] = Exception,
                   name: str = None,
                   fallback_function: Callable = None,
                   fallback_function_with_exception: Callable = None):
    """

            :param max_attempts: Max failed attempts until the circuit breaker should be opened
            :param reset_timeout:
            Number of milliseconds until an opened circuit breaker should become half-opened and allow new attempts
            :param expected_exception: The
            exception the circuit breaker should expect as a failure (e.g. ConnectionError, RequestException)
            :param
            name: Name of the circuit breaker instance. Mostly useful if you intend to use the CircuitBreakerManager.
            :param fallback_function: A function to use as fallback if the circuit breaker is opened.
            :param fallback_function_with_exception: A function to use as fallback if the circuit breaker is opened.
            The first argument supplied to it will be the most recent exception (i.e.
            fallback_function_with_exception(last_exception, *args, **kwargs))
    """

    # To be able to use decorator without parentheses
    # if no arguments are provided. Hate it but gets the job done.
    if callable(max_attempts):
        return CircuitBreakerClass().decorate(max_attempts)
    else:
        return CircuitBreakerClass(
            max_attempts=max_attempts,
            reset_timeout=reset_timeout,
            sliding_window_length=sliding_window_length,
            expected_exception=expected_exception,
            name=name,
            fallback_function=fallback_function,
            fallback_function_with_exception=fallback_function_with_exception)

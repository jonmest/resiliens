#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

from datetime import timedelta, datetime
from functools import wraps
from inspect import isgeneratorfunction
from math import ceil, floor
from time import monotonic
from types import TracebackType
from typing import Union, Callable, Optional, Type, Any

from src.resiliens.circuit_breaker.CircuitBreakerException import CircuitBreakerException
from src.resiliens.circuit_breaker.CircuitBreakerState import CircuitBreakerState
from src.resiliens.circuit_breaker.CircuitBreakerStatus import CircuitBreakerStatus
from src.resiliens.circuit_breaker.SlidingWindow import SlidingWindow
from src.resiliens.circuit_breaker.manager.CircuitBreakerManager import CircuitBreakerManager


class CircuitBreakerClass:
    _failure_threshold: int
    _reset_timeout: Union[float, int]
    _expected_exception: Type[BaseException]
    _fallback_function: Callable
    _fallback_function_with_exception: Callable
    _sliding_window: SlidingWindow

    def __init__(self,
                 failures: int = 5,
                 reset_timeout: Union[float, int] = 20_000,
                 sliding_window_size: int = None,
                 expected_exception: Type[BaseException] = Exception,
                 name: str = None,
                 fallback_function: Callable = None,
                 fallback_function_with_exception: Callable = None):
        """
        :param failures: Number of failures that need to be reached for the circuit breaker to be opened. If the
        argument "sliding_window_size" is supplied, this will be the total number of failures in the window. If it is
        not supplied, it will be the number of failures in a row.
        :param reset_timeout: Number of milliseconds until an opened circuit breaker should become half-open and allow new attempts
        :param sliding_window_size makes the circuit breaker keep a sliding window of the most recent results (failure, success). If
        the argument "failures" number of failures are in the window, the circuit breaker will open.
        :param expected_exception: The exception the circuit breaker should expect as a failure (e.g. ConnectionError, RequestException)
        :param name: Name of the circuit breaker instance. Mostly useful if you intend to use the CircuitBreakerManager.
        :param fallback_function: A function to use as fallback if the circuit breaker is opened.
        :param fallback_function_with_exception: A function to use as fallback if the circuit breaker is opened. The first
        argument supplied to it will be the most recent exception (i.e. fallback_function_with_exception(
        last_exception, *args, **kwargs))
        """

        self._state = CircuitBreakerState(status=CircuitBreakerStatus.closed,
                                          fail_count=0,
                                          last_failure=None,
                                          opened=monotonic())
        self._failure_threshold = failures
        self._reset_timeout = reset_timeout / 1000  # From milliseconds to seconds
        self._expected_exception = expected_exception
        self._fallback_function = fallback_function
        self._fallback_function_with_exception = fallback_function_with_exception
        self._name = name
        if sliding_window_size:
            self._sliding_window = SlidingWindow(sliding_window_size)

    @property
    def status(self):
        if self._state.status == CircuitBreakerStatus.open and self.open_seconds_remaining <= 0:
            return CircuitBreakerStatus.half_open
        return self._state.status

    @property
    def failure_threshold(self):
        return self._failure_threshold

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
        return self.status == CircuitBreakerStatus.closed

    @property
    def opened(self):
        return self.status == CircuitBreakerStatus.open

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
                    return call(self.fallback_function, *args, **kwargs)
                elif self._fallback_function_with_exception:
                    return call(self._fallback_function_with_exception, (self.last_failure, *args), **kwargs)
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
        self._state.status = CircuitBreakerStatus.closed
        self._state.last_failure = None
        self._state.fail_count = 0
        if self._sliding_window:
            self._sliding_window.add(True)

    def __call_failed(self) -> None:
        self._state.fail_count += 1
        if self._sliding_window:
            self._sliding_window.add(False)
            if self._sliding_window.get_failure_count(
            ) >= self._failure_threshold:
                self._state.status = CircuitBreakerStatus.open
                self._state.opened = monotonic()
        elif self._state.fail_count >= self._failure_threshold:
            self._state.status = CircuitBreakerStatus.open
            self._state.opened = monotonic()

    def force_open(self) -> None:
        self._state.status = CircuitBreakerStatus.open
        self._state.opened = monotonic()

    def force_reset(self) -> None:
        self.__call_succeeded()

    def __str__(self, *args, **kwargs) -> str:
        return self._name


def CircuitBreaker(failures: int = 5,
                   reset_timeout: Union[float, int] = 20_000,
                   sliding_window_size: int = None,
                   expected_exception: Type[BaseException] = Exception,
                   name: str = None,
                   fallback_function: Callable = None,
                   fallback_function_with_exception: Callable = None):
    """
    :param failures: Number of failures that need to be reached for the circuit breaker to be opened. If the
    argument "sliding_window_size" is supplied, this will be the total number of failures in the window. If it is
    not supplied, it will be the number of failures in a row.
    :param reset_timeout: Number of milliseconds until an opened circuit breaker should become half-open and allow new attempts
    :param sliding_window_size makes the circuit breaker keep a sliding window of the most recent results (failure, success). If
    the argument "failures" number of failures are in the window, the circuit breaker will open.
    :param expected_exception: The exception the circuit breaker should expect as a failure (e.g. ConnectionError, RequestException)
    :param name: Name of the circuit breaker instance. Mostly useful if you intend to use the CircuitBreakerManager.
    :param fallback_function: A function to use as fallback if the circuit breaker is opened.
    :param fallback_function_with_exception: A function to use as fallback if the circuit breaker is opened. The first
    argument supplied to it will be the most recent exception (i.e. fallback_function_with_exception(
    last_exception, *args, **kwargs))
    """

    # We check this to be able to use decorator without parentheses
    # if no arguments are provided. Hacky it but gets the job done.
    if callable(failures):
        return CircuitBreakerClass().decorate(failures)
    else:
        return CircuitBreakerClass(
            failures=failures,
            reset_timeout=reset_timeout,
            sliding_window_size=sliding_window_size,
            expected_exception=expected_exception,
            name=name,
            fallback_function=fallback_function,
            fallback_function_with_exception=fallback_function_with_exception)

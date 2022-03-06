#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester
import time
from functools import wraps
from inspect import isgeneratorfunction
from typing import Callable, Type, Any, Union


class RetryableClass:
    max_retries: int
    backoff: Union[int, float]
    backoff_exponent: Union[int, float]
    fallback_function: Callable

    _current_attempts: int
    _last_failure: Exception

    def __init__(self, max_retries: int = 3, backoff: Union[int, float] = 1000,
                 backoff_multiplier: Union[int, float] = None,
                 fallback: Callable = None,
                 expected_exception: Type[BaseException] = Exception):
        """
        :param max_retries: Max number of retries until it should give up.
        :param backoff: Backoff time in MILLISECONDS. If you don't set a backoff_exponent, this
        will be constant (e.g. 1000 milliseconds for all retries). If you do set a backoff_exponent,
        the backoff time will increase for every retry.
        :param backoff_exponent: Exponent to make the backoff time increase for every attempt
        (backoff * (retry_count ** backoff_exponent)). Say you set it to 2. On the second attempt,
        the backoff time will be multiplied with 2. On the fourth attempt, the backoff time will be multiplied with 8.
        :param fallback: Fallback function to get called in case the max retries limit has been reached. Optional,
        if not set the last exception will just get thrown.
        :param expected_exception: For what exceptions should we attempt to retry? Default is any exception, but you may
        want this to be more fine-grained (e.g. ConnectionError, RequestException)
        """
        self.max_retries = max_retries
        self.backoff = backoff / 1000  # Milliseconds to seconds
        self.fallback_function = fallback
        self._current_attempts = 0
        self.backoff_exponent = backoff_multiplier
        self._expected_exception = expected_exception

    def __call__(self, decorated_function=None):
        return self.decorate(decorated_function)

    @staticmethod
    def call(func, *args, **kwargs) -> Any:
        return func(*args, **kwargs)

    @staticmethod
    def call_generator(func, *args, **kwargs):
        for el in func(*args, **kwargs):
            yield el

    def get_backoff_time(self):
        if self.backoff_exponent:
            return max(self._current_attempts ** self.backoff_exponent, 1) * self.backoff
        else:
            return self.backoff

    def decorate(self, function_to_decorate: Callable = None) -> Callable:
        if isgeneratorfunction(function_to_decorate):
            call = self.call_generator
        else:
            call = self.call

        @wraps(function_to_decorate)
        def wrapper(*args, **kwargs):
            self.retry_if_needed(call, function_to_decorate, *args, **kwargs)

        return wrapper

    def retry_if_needed(self, call, function_to_decorate, *args, **kwargs):
        while self._current_attempts < self.max_retries:
            try:
                return call(function_to_decorate, *args, **kwargs)
            except Exception as e:
                if issubclass(e.__class__, self._expected_exception):
                    self._current_attempts += 1
                    self._last_failure = e
                    if self._current_attempts < self.max_retries:
                        time.sleep(self.get_backoff_time())
                else:
                    raise e


# The decorator itself
def Retryable(max_retries: int = 3, backoff: Union[int, float] = 1000,
              backoff_multiplier: Union[int, float] = None,
              fallback: Callable = None,
              expected_exception: Type[BaseException] = Exception):
    """
            :param max_retries: Max number of retries until it should give up.
            :param backoff: Backoff time in MILLISECONDS. If you don't set a backoff_exponent, this
            will be constant (e.g. 1000 milliseconds for all retries). If you do set a backoff_exponent,
            the backoff time will increase for every retry.
            :param backoff_exponent: Exponent to make the backoff time increase for every attempt
            (backoff * (retry_count ** backoff_exponent)). Say you set it to 2. On the second attempt,
            the backoff time will be multiplied with 2. On the fourth attempt, the backoff time will be multiplied with 8.
            :param fallback: Fallback function to get called in case the max retries limit has been reached. Optional,
            if not set the last exception will just get thrown.
            :param expected_exception: For what exceptions should we attempt to retry? Default is any exception, but you may
            want this to be more fine-grained (e.g. ConnectionError, RequestException)
            """

    # To be able to use decorator without parentheses
    # if no arguments are provided. Hate it but gets the job done.
    if callable(max_retries):
        return RetryableClass().decorate(max_retries)
    else:
        return RetryableClass(
            max_retries=max_retries,
            backoff=backoff,
            backoff_multiplier=backoff_multiplier,
            fallback=fallback,
            expected_exception=expected_exception)

#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

from functools import wraps
from inspect import isgeneratorfunction
from typing import Callable, Type, Any


class FallbackClass:
    fallback: Callable
    fallback_function: Callable
    expected_exception: Exception

    def __init__(self,
                 fallback: Callable = None,
                 fallback_function: Callable = None,
                 expected_exception: Type[BaseException] = Exception):
        self.fallback = fallback
        self.fallback_function = fallback_function
        self._expected_exception = expected_exception

        if not self.fallback and not self.fallback_function:
            raise TypeError(
                "Fallback decorator requires either a \"fallback\" or \"fallback_exception\" argument and "
                "neither was given.")
        if self.fallback and not callable(self.fallback):
            raise TypeError(
                "Argument \"fallback\" must be callable (i.e. a function)")
        if self.fallback_function and not callable(self.fallback_function):
            raise TypeError(
                "Argument \"fallback_exception\" must be callable (i.e. a function)"
            )

    def __call__(self, decorated_function):
        return self.decorate(decorated_function)

    @staticmethod
    def call(func, *args, **kwargs) -> Any:
        return func(*args, **kwargs)

    @staticmethod
    def call_generator(func, *args, **kwargs):
        for el in func(*args, **kwargs):
            yield el

    def decorate(self, function_to_decorate: Callable = None) -> Callable:
        call = self.call_generator if isgeneratorfunction(
            function_to_decorate) else self.call

        @wraps(function_to_decorate)
        def wrapper(*args, **kwargs):
            return self.try_catch_fallback(call, function_to_decorate, *args,
                                           **kwargs)

        return wrapper

    def try_catch_fallback(self, call, function_to_decorate, *args, **kwargs):
        try:
            return call(function_to_decorate, *args, **kwargs)
        except Exception as e:
            if issubclass(e.__class__, self._expected_exception):
                if self.fallback_function:
                    return call(self.fallback_function, (e, *args), **kwargs)
                else:
                    return call(self.fallback, *args, **kwargs)
            else:
                raise e


def WithFallback(fallback: Callable = None,
                 fallback_function: Callable = None,
                 for_exception: Type[BaseException] = Exception):
    """
    Provide a fallback function for the decorated function in case an exception is thrown. NOTE: The fallback
    function must take the same number of arguments as the decorated function. Optionally, the fallback function may
    take the thrown exception as a first argument, followed by the arguments of the decorated function - in that
    case, use the fallback_exception parameter to specify the fallback function.
    :param fallback: Reference to the fallback function - note that it needs to same function signature as the decorated function.
    :param fallback_function: Reference to the fallback function that takes the thrown exception as an additional argument
    - note that it needs to same function signature as the decorated function.
    :param for_exception: Exception class you want to use fallback for. Default is the base Exception, but you may only want
    to use the fallback for, say, IOError and in that case you should specify it here.
    """
    return FallbackClass(fallback=fallback,
                         fallback_function=fallback_function,
                         expected_exception=for_exception)

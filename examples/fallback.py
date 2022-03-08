#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester
from resiliens import WithFallback


def fallback_exception(exception, foo):
    print("Original argument:", foo, "- Exception:", exception)


def fallback(foo):
    print("Original argument:", foo)


@WithFallback(fallback_exception=fallback_exception)
def some_function(foo):
    # Try to do something and fail
    raise ConnectionError()


@WithFallback(fallback)
def some_other_function(foo):
    # Try to do something and fail
    raise ConnectionError()


if __name__ == "__main__":
    some_function(foo="bar")
    some_other_function(foo="fuzz")

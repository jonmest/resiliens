#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester
from resiliens import CircuitBreaker


def fallback(exception: Exception, foo):
    print(f"Another function tried to do something foo={foo} and failed:", exception)


# After 5 failures, open the circuit breaker.
# Pass exception and original arguments to fallback function
@CircuitBreaker(failures=5, fallback_exception=fallback)
def underlying_function(foo):
    # Pretend we're attempting to make a network request here
    raise ConnectionError()


if __name__ == "__main__":
    for _ in range(0, 10):
        underlying_function(foo="bar")

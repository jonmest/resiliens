#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester
from resiliens import CircuitBreaker

data_store = {"underlying_function_call_count": 0}


# After 5 failures, open the circuit breaker.
@CircuitBreaker(failures=5)
def underlying_function():
    data_store["underlying_function_call_count"] += 1
    # Pretend we're attempting to make a network request here
    raise ConnectionError()


if __name__ == "__main__":
    for _ in range(0, 10):
        try:
            underlying_function()
        except Exception as e:
            print(e)

    print("The underlying function got called",
          data_store["underlying_function_call_count"], "times")

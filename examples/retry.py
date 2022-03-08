#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester
from resiliens import Retryable

data_store = {"retry_count": 0}


def fallback(exception):
    print("Couldn't reach the imaginary API but at least I tried",
          data_store["retry_count"], "times.")
    print("It was that damn exception messing things up:", exception)


@Retryable(max_retries=5, backoff=500, fallback_exception=fallback)
def some_function():
    data_store["retry_count"] += 1
    # Try to do something and fail
    raise ConnectionError()


if __name__ == "__main__":
    some_function()

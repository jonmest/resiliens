#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

strtimeformat = "%m/%d/%Y, %H:%M:%S"


class CircuitBreakerException(Exception):

    def __init__(self, circuit_breaker, *args):
        super(CircuitBreakerException, self).__init__(*args)
        self._circuit_breaker = circuit_breaker

    def __str__(self, *args, **kwargs):
        return f"[Circuit breaker: {self._circuit_breaker.name}] Reached {self._circuit_breaker.failure_count}" \
               f" failures and will be open until {self._circuit_breaker.open_until.strftime(strtimeformat)}" \
               f" ({self._circuit_breaker.open_seconds_remaining} sec remaining)" \
               f" (Last failure: {repr(self._circuit_breaker.last_failure)})"

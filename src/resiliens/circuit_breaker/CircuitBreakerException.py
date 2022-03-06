#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

class CircuitBreakerException(Exception):
    def __init__(self, circuit_breaker, *args):
        super(CircuitBreakerException, self).__init__(*args)
        self._circuit_breaker = circuit_breaker

    def __str__(self, *args, **kwargs):
        return '[Circuit breaker: %s] Reached %d failures and will be open until' \
               ' %s (%d sec remaining) (_last_failure: %r)' % (
                   self._circuit_breaker.name,
                   self._circuit_breaker.failure_count,
                   self._circuit_breaker.open_until,
                   round(self._circuit_breaker.open_seconds_remaining),
                   self._circuit_breaker._last_failure,
               )

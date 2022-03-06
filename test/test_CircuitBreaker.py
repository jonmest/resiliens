import time
import unittest

from src.resiliens.circuit_breaker import CircuitBreaker
from src.resiliens.circuit_breaker import CircuitBreakerStatus


class TestCircuitBreaker(unittest.TestCase):
    MAX_ATTEMPTS: int = 5
    WINDOW_SIZE: int = 10

    failed_count: int
    successful_count: int
    circuit_breaker: CircuitBreaker

    def setUp(self) -> None:
        self.failed_count = 0
        self.successful_count = 0

    @CircuitBreaker(max_attempts=MAX_ATTEMPTS,
                    sliding_window_length=WINDOW_SIZE)
    def fake_successful_http_call(self):
        self.successful_count += 1
        return True

    @CircuitBreaker(max_attempts=MAX_ATTEMPTS,
                    sliding_window_length=WINDOW_SIZE)
    def fake_failed_http_call(self):
        self.failed_count += 1
        raise Exception()

    def test_slidingWindow50Percent_circuitBreakerOpensAfter5Failures(self):
        should_fail = True
        reset_time = 1000

        @CircuitBreaker(max_attempts=self.MAX_ATTEMPTS,
                        reset_timeout=reset_time,
                        sliding_window_length=self.WINDOW_SIZE)
        def test_func():
            if should_fail:
                self.failed_count += 1
                raise Exception()
            self.successful_count += 1

        for i in range(0, self.MAX_ATTEMPTS * 2):
            try:
                test_func()
            except Exception as ignored:
                pass
        expected = self.MAX_ATTEMPTS
        actual = self.failed_count
        self.assertEqual(expected, actual)

        should_fail = False
        time.sleep(reset_time / 1000)

        test_func()
        expected = 1
        actual = self.successful_count
        self.assertEqual(expected, actual)

    def test_circuitBreakerIsGivenName_getNameProperty_returnsRightName(self):
        self.circuit_breaker = CircuitBreaker(name="CB1")

        expected = "CB1"
        actual = self.circuit_breaker.name

        self.assertEqual(expected, actual)

    def test_circuitBreakerIsGivenMaxAttempts_getMaxAttemptsProperty_returnsRightMaxAttempts(
            self):
        self.circuit_breaker = CircuitBreaker(max_attempts=100)

        expected = 100
        actual = self.circuit_breaker.max_attempts

        self.assertEqual(expected, actual)

    def test_circuitBreakerIsInitialized_circuitBreakerStatusIsClosed(self):
        self.circuit_breaker = CircuitBreaker()

        expected = CircuitBreakerStatus.CLOSED
        actual = self.circuit_breaker.status

        self.assertEqual(expected, actual)

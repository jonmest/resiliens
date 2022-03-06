import unittest

from src.resiliens.circuit_breaker import CircuitBreaker
from src.resiliens.circuit_breaker import CircuitBreakerStatus


class TestCircuitBreaker(unittest.TestCase):
    circuit_breaker: CircuitBreaker

    def test_circuitBreakerIsGivenName_getNameProperty_returnsRightName(self):
        self.circuit_breaker = CircuitBreaker(name="CB1")

        expected = "CB1"
        actual = self.circuit_breaker.name

        self.assertEqual(expected, actual)

    def test_circuitBreakerIsGivenMaxAttempts_getMaxAttemptsProperty_returnsRightMaxAttempts(self):
        self.circuit_breaker = CircuitBreaker(max_attempts=100)

        expected = 100
        actual = self.circuit_breaker.max_attempts

        self.assertEqual(expected, actual)

    def test_circuitBreakerIsInitialized_circuitBreakerStatusIsClosed(self):
        self.circuit_breaker = CircuitBreaker()

        expected = CircuitBreakerStatus.CLOSED
        actual = self.circuit_breaker.status

        self.assertEqual(expected, actual)


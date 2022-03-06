from time import sleep

from unittest.mock import Mock, patch
from pytest import raises

from src.resiliens.circuit_breaker import CircuitBreaker, CircuitBreakerManager, CircuitBreakerException, CircuitBreakerStatus


def fake_successful_http_call():
    return True


@CircuitBreaker()
def circuit_success():
    return fake_successful_http_call()


@CircuitBreaker(max_attempts=1, name="circuit_failure")
def circuit_failure():
    raise IOError()


@CircuitBreaker(max_attempts=1, name="circuit_generator_failure")
def circuit_generator_failure():
    fake_successful_http_call()
    yield 1
    raise IOError()


@CircuitBreaker(max_attempts=1, name="max_attempts_1")
def circuit_max_attempts_1():
    return fake_successful_http_call()


@CircuitBreaker(max_attempts=2, reset_timeout=1, name="max_attempts_2")
def circuit_max_attempts_2_timeout_1():
    return fake_successful_http_call()


@CircuitBreaker(max_attempts=3, reset_timeout=1, name="max_attempts_3")
def circuit_max_attempts_3_timeout_1():
    return fake_successful_http_call()


def test_circuit_pass_through():
    assert circuit_success() is True


def test_circuitbreaker_monitor():
    assert CircuitBreakerManager.all_closed() is True
    assert len(list(CircuitBreakerManager.get_circuits())) == 6
    assert len(list(CircuitBreakerManager.get_closed())) == 6
    assert len(list(CircuitBreakerManager.get_open())) == 0

    with raises(IOError):
        circuit_failure()

    assert CircuitBreakerManager.all_closed() is False
    assert len(list(CircuitBreakerManager.get_circuits())) == 6
    assert len(list(CircuitBreakerManager.get_closed())) == 5
    assert len(list(CircuitBreakerManager.get_open())) == 1


@patch('test_integration.fake_successful_http_call', return_value=True)
def test_threshold_hit_prevents_consequent_calls(mock_remote):
    # type: (Mock) -> None
    mock_remote.side_effect = IOError('Connection refused')
    circuitbreaker = CircuitBreakerManager.get('max_attempts_1')

    assert circuitbreaker.closed

    with raises(IOError):
        circuit_max_attempts_1()

    assert circuitbreaker.opened

    with raises(CircuitBreakerException):
        circuit_max_attempts_1()

    mock_remote.assert_called_once_with()


@patch('test_integration.fake_successful_http_call', return_value=True)
def test_circuitbreaker_recover_half_open(mock_remote):
    circuitbreaker = CircuitBreakerManager.get('max_attempts_3')

    assert circuitbreaker.closed
    assert circuitbreaker.status == CircuitBreakerStatus.CLOSED

    assert circuit_max_attempts_3_timeout_1()

    mock_remote.side_effect = IOError('Connection refused')

    with raises(IOError):
        circuit_max_attempts_3_timeout_1()
    assert circuitbreaker.closed
    assert circuitbreaker.failure_count == 1

    with raises(IOError):
        circuit_max_attempts_3_timeout_1()
    assert circuitbreaker.closed
    assert circuitbreaker.failure_count == 2

    with raises(IOError):
        circuit_max_attempts_3_timeout_1()

    assert circuitbreaker.opened
    assert circuitbreaker.status == CircuitBreakerStatus.OPEN
    assert circuitbreaker.failure_count == 3
    assert 0 < circuitbreaker.open_seconds_remaining <= 1

    with raises(CircuitBreakerException):
        circuit_max_attempts_3_timeout_1()
    assert circuitbreaker.opened
    assert circuitbreaker.failure_count == 3
    assert 0 < circuitbreaker.open_seconds_remaining <= 1

    with raises(CircuitBreakerException):
        circuit_max_attempts_3_timeout_1()
    assert circuitbreaker.opened
    assert circuitbreaker.failure_count == 3
    assert 0 < circuitbreaker.open_seconds_remaining <= 1

    sleep(1)

    assert not circuitbreaker.closed
    assert circuitbreaker.open_seconds_remaining < 0
    assert circuitbreaker.status == CircuitBreakerStatus.HALF_OPEN

    with raises(IOError):
        circuit_max_attempts_3_timeout_1()
    assert circuitbreaker.opened
    assert circuitbreaker.failure_count == 4
    assert 0 < circuitbreaker.open_seconds_remaining <= 1

    with raises(CircuitBreakerException):
        circuit_max_attempts_3_timeout_1()


@patch('test_integration.fake_successful_http_call', return_value=True)
def test_circuitbreaker_reopens_after_successful_calls(mock_remote):
    circuitbreaker = CircuitBreakerManager.get('max_attempts_2')

    assert str(circuitbreaker) == 'max_attempts_2'

    assert circuitbreaker.closed
    assert circuitbreaker.status == CircuitBreakerStatus.CLOSED
    assert circuitbreaker.failure_count == 0

    assert circuit_max_attempts_2_timeout_1()

    mock_remote.side_effect = IOError('Connection refused')

    with raises(IOError):
        circuit_max_attempts_2_timeout_1()
    assert circuitbreaker.closed
    assert circuitbreaker.failure_count == 1

    with raises(IOError):
        circuit_max_attempts_2_timeout_1()

    assert circuitbreaker.opened
    assert circuitbreaker.status == CircuitBreakerStatus.OPEN
    assert circuitbreaker.failure_count == 2
    assert 0 < circuitbreaker.open_seconds_remaining <= 1

    with raises(CircuitBreakerException):
        circuit_max_attempts_2_timeout_1()
    assert circuitbreaker.opened
    assert circuitbreaker.failure_count == 2
    assert 0 < circuitbreaker.open_seconds_remaining <= 1

    mock_remote.side_effect = None

    with raises(CircuitBreakerException):
        circuit_max_attempts_2_timeout_1()
    assert circuitbreaker.opened
    assert circuitbreaker.failure_count == 2
    assert 0 < circuitbreaker.open_seconds_remaining <= 1

    sleep(1)

    assert not circuitbreaker.closed
    assert circuitbreaker.failure_count == 2
    assert circuitbreaker.open_seconds_remaining < 0
    assert circuitbreaker.status == CircuitBreakerStatus.HALF_OPEN

    assert circuit_max_attempts_2_timeout_1()

    assert circuitbreaker.closed
    assert circuitbreaker.status == CircuitBreakerStatus.CLOSED
    assert circuitbreaker.failure_count == 0

    assert circuit_max_attempts_2_timeout_1()
    assert circuit_max_attempts_2_timeout_1()
    assert circuit_max_attempts_2_timeout_1()


@patch("test_integration.fake_successful_http_call", return_value=True)
def test_circuitbreaker_handles_generator_functions(mock_remote):
    circuitbreaker = CircuitBreakerManager.get("circuit_generator_failure")
    assert circuitbreaker.closed

    with raises(IOError):
        list(circuit_generator_failure())

    assert circuitbreaker.opened

    with raises(CircuitBreakerException):
        list(circuit_generator_failure())

    mock_remote.assert_called_once_with()

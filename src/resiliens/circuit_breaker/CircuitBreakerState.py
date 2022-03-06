#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

from typing import Any

from src.resiliens.circuit_breaker.CircuitBreakerStatus import CircuitBreakerStatus


class CircuitBreakerState:
    _status: str
    fail_count: int
    last_failure: Any
    opened: float

    def __init__(self, status: str,
                 fail_count: int = 0,
                 last_failure=None,
                 opened: float = 0):
        self.fail_count = fail_count
        self.status = status
        self.last_failure = last_failure
        self.opened = opened

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status: str):
        if CircuitBreakerStatus.is_valid_status(new_status):
            self._status = new_status
        # Todo raise exception

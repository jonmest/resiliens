#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

class _CircuitBreakerStatus:
    _CLOSED: str = 'CLOSED'
    _OPEN: str = 'OPEN'
    _HALF_OPEN: str = 'HALF_OPEN'

    @property
    def CLOSED(self) -> str:
        return self._CLOSED

    @property
    def OPEN(self) -> str:
        return self._OPEN

    @property
    def HALF_OPEN(self) -> str:
        return self._HALF_OPEN

    def is_valid_status(self, status: str):
        return status in (self._OPEN, self._HALF_OPEN, self._CLOSED)


CircuitBreakerStatus = _CircuitBreakerStatus()

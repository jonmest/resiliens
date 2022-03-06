#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester


class CircuitBreakerManager:
    circuit_breakers = {}

    @classmethod
    def register(cls, circuit_breaker):
        cls.circuit_breakers[circuit_breaker.name] = circuit_breaker

    @classmethod
    def all_closed(cls) -> bool:
        return len(list(cls.get_open())) == 0

    @classmethod
    def get_circuits(cls):
        return cls.circuit_breakers.values()

    @classmethod
    def get(cls, name: str):
        return cls.circuit_breakers.get(name)

    @classmethod
    def get_open(cls):
        for circuit in cls.get_circuits():
            if circuit.opened:
                yield circuit

    @classmethod
    def get_closed(cls):
        for circuit in cls.get_circuits():
            if circuit.closed:
                yield circuit

    @classmethod
    def force_open(cls, name: str) -> None:
        circuit_breaker = cls.circuit_breakers.get(name)
        circuit_breaker.force_open()

    @classmethod
    def force_reset(cls, name: str) -> None:
        circuit_breaker = cls.circuit_breakers.get(name)
        circuit_breaker.force_reset()

    @classmethod
    def force_all_open(cls) -> None:
        for circuit_breaker in cls.circuit_breakers.values():
            circuit_breaker.force_open()

    @classmethod
    def force_all_reset(cls) -> None:
        for circuit_breaker in cls.circuit_breakers.values():
            circuit_breaker.force_reset()

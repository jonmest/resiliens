#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester
from typing import List


class SlidingWindow:
    _internal_list: List[bool]
    _window_length: int

    def __init__(self, window_length: int):
        self._internal_list = []
        self._window_length = window_length

    def add(self, result: bool):
        if len(self._internal_list) >= self._window_length:
            self._internal_list.pop(0)
        self._internal_list.append(result)

    def get_failure_count(self):
        return sum(map(lambda result: not result, self._internal_list))

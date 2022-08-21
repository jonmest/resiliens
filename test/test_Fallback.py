#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester

import unittest

from src.resiliens.fallback.Fallback import WithFallback


def fallback_for_function(foo, bar):
    return foo, bar


@WithFallback(fallback_for_function)
def failing_function(foo, bar):
    raise Exception


@WithFallback(fallback_for_function)
def succeeding_function(foo, bar):
    return bar, foo


class TestFallback(unittest.TestCase):
    fallback_got_called: bool

    def setUp(self) -> None:
        self.fallback_got_called = False

    def method_fallback(self):
        self.fallback_got_called = True

    @WithFallback(method_fallback)
    def failing_method_with_fallback(self):
        raise Exception()

    @WithFallback(method_fallback)
    def succeeding_method_with_fallback(self):
        return True

    def test_methodFails_fallbackGetsCalled(self):
        self.failing_method_with_fallback()
        self.assertTrue(self.fallback_got_called)

    def test_methodSucceeds_fallbackIsNotCalled(self):
        res = self.succeeding_method_with_fallback()
        self.assertTrue(res)
        self.assertFalse(self.fallback_got_called)

    def test_fallbackWithIOErrorAsExpected_regularExceptionIsThrown_fallbackNotCalled(
            self):

        @WithFallback(fallback=self.method_fallback,
                      for_exception=IOError)
        def bogus_function(_self):
            raise Exception()

        self.assertRaises(Exception, bogus_function)

    @WithFallback(fallback=method_fallback, for_exception=IOError)
    def bogus_function(self):
        raise IOError()

    def test_fallbackWithIOErrorAsExpected_IOErrorIsThrown_fallbackIsCalled(
            self):
        self.bogus_function()
        self.assertTrue(self.fallback_got_called)

    def test_functionFails_fallbackIsCalled(self):
        foo, bar = 1, 2
        foo2, bar2 = failing_function(foo, bar)
        self.assertEqual(bar, bar2)
        self.assertEqual(foo, foo2)

    def test_functionSucceeds_fallbackIsNotCalled(self):
        foo, bar = 1, 2
        foo2, bar2 = failing_function(foo, bar)
        self.assertEqual(bar, bar2)
        self.assertEqual(foo, foo2)

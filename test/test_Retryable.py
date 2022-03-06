#  Copyright (c) 2022 - Thumos - Jon Cavallie Mester
import unittest

from src.resiliens.retryable import Retryable


class TestRetryable(unittest.TestCase):
    MAX_ATTEMPTS: int = 5
    BACKOFF: int = 100

    failed_count: int
    successful_count: int

    def setUp(self) -> None:
        self.failed_count = 0
        self.successful_count = 0

    @Retryable(max_retries=MAX_ATTEMPTS)
    def fake_successful_http_call(self):
        self.successful_count += 1
        return True

    @Retryable(max_retries=MAX_ATTEMPTS)
    def fake_failed_http_call(self):
        self.failed_count += 1
        raise Exception()

    def test_callRaisesException_retryIsDoneRightNumberOfTimes(self):
        self.fake_failed_http_call()
        expected = self.MAX_ATTEMPTS
        actual = self.failed_count

        self.assertEqual(expected, actual)

    def test_callSucceeds_noRetryIsPerformed(self):
        self.fake_successful_http_call()
        expected = 1
        actual = self.successful_count

        self.assertEqual(expected, actual)

    def test_callFailsWithUnexpectedException_noRetryIsPerformedAndExceptionIsRaised(self):
        @Retryable(max_retries=self.MAX_ATTEMPTS, expected_exception=IOError)
        def failed_http_call_with_unexpected_exception():
            self.failed_count += 1
            raise Exception()

        self.assertRaises(Exception, failed_http_call_with_unexpected_exception)

    def test_decoratorWithNoArguments(self):
        @Retryable
        def failed_http_call_with_unexpected_exception():
            self.failed_count += 1
            raise Exception()

        failed_http_call_with_unexpected_exception()
        expected = 3
        actual = self.failed_count
        self.assertEqual(expected, actual)

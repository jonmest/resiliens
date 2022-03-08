<p align="center">
    <img src="logo.png" alt="Resiliens"/><br/>
    A Python package for resilient programming. <br/><br/>
    <a href="https://github.com/jonmest/resiliens/actions/workflows/python-package.yml"><img src="https://github.com/jonmest/resiliens/actions/workflows/python-package.yml/badge.svg" alt="Build, lint and test"/></a>
    <a href="https://deepsource.io/gh/jonmest/resiliens/?ref=repository-badge"><img src="https://deepsource.io/gh/jonmest/resiliens.svg/?label=active+issues&show_trend=true&token=03a2Qus_Z4mOopqLDJ2yMqdp" alt="Build, lint and test"/></a>
</p>

# About
If you want to make your Python code more resilient, use the Resiliens library! Quickly wrap your existing functions
with the `@Retryable` decorator to automatically retry on failure, and with `@CircuitBreaker` to prevent calls to the
function if it has exceeded a failure limit.

Currently, there are two decorators provided:
1. Retryable - automatically re-calls the wrapped function if an exception is raised.
2. CircuitBreaker - prevent calls to the wrapped function if it is known to currently be failing.
    
The documentation here will be brief, but hopefully you'll be able to make sense of it by reading the docstrings.

## Installation
Built for Python >=3.6
```bash
pip install Resiliens
```

## 1. Retryable
You can use the `@Retryable` decorator on any function to automatically retry calling it in case it throws an exception. One use-case would be if you make a remote call to an external API which returns the HTTP status code 500. Maybe it's just a very temporary issue, in which case you might as well try a few more times.

```python
# Use default configuration
@Retryable
def get_github():
    res = requests.get('https://api.github.com')
    if res.status == '500':
        raise ThisFailedError()

# Configure your own max retries, backoff time
# between attempts, and more
@Retryable(max_retries=5, backoff=1000)
def get_github():
    requests.get('https://api.github.com')
    if res.status == '500':
            raise ThisFailedError()
```

## 2. CircuitBreaker
If you make a remote call, and it keeps failing, you may want to stop making this call to save your API usage quota or lower the response time of something that would be failing anyway. In that case, a circuit breaker comes handy.

Currently, this decorator stops calling the decorated function after a configured number of failures in a row (the circuit breaker "opens") and immediately returns the most recent exception instead. After a wait period, the circuit breaker allows new calls to the decorated function. You can also supply the optional argument `sliding_window_length` - then the circuit breaker will keep a sliding window of the most recent results in a list. If the number of failures in the sliding window reach the `max_attempts` threshold, the circuit breaker will open.

```python
@CircuitBreaker
def get_github():
    res = requests.get('https://api.github.com')
    if res.status == '500':
        raise ThisFailedError()

# Configure your own max failed attempts, 
# reset_timeout and more
@CircuitBreaker(max_attempts=5, reset_timeout=1000)
def get_github():
    requests.get('https://api.github.com')
    if res.status == '500':
            raise ThisFailedError()
```
# Expected exceptions
Both decorators have the parameter `expected_exception`. This is the exception they should consider as an expected failure, say that an API is unreachable. If that exception, or a subclass of it, gets raised in the decorated function, Retryable will retry as intended, and CircuitBreaker will count it as a failure and eventually open if it keeps getting raised. If, however, an exception gets raised that is not of that exception type, or a subclass of it, Retryably will not retry and CircuitBreaker will not count it as a failure. By default, they consider all exceptions as expected, but ideally you should set this in a more fine-grained way - e.g. ConnectionError, RequestException.

# Fallback functions
It may be the case that a function decorated with @Retryable never succeeds despite retrying a bunch of times. By default, it will just raise the last exception. However, you can set a fallback function that gets called after all retries are exhausted, for example to provide a fallback return value or do something else.
Same goes for @CircuitBreaker - by default, if the circuit breaker is open it just raises the most recent exception again. You can however supply a fallback function here as well.

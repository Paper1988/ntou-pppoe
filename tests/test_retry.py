from ntou_pppoe.core.retry import RetryController


def test_initial_attempt_is_zero():
    """A new retry controller should start at attempt zero."""

    retry = RetryController(
        initial_delay=5,
        max_delay=60,
        max_attempts=5,
    )

    assert retry.attempt == 0


def test_retry_is_allowed_before_max_attempts():
    """Retries should be allowed while the limit is not reached."""

    retry = RetryController(
        initial_delay=5,
        max_delay=60,
        max_attempts=5,
    )

    assert retry.can_retry() is True


def test_exponential_backoff():
    """Retry delays should increase exponentially."""

    retry = RetryController(
        initial_delay=5,
        max_delay=60,
        max_attempts=5,
    )

    delays = [
        retry.next_delay(),
        retry.next_delay(),
        retry.next_delay(),
        retry.next_delay(),
        retry.next_delay(),
    ]

    assert delays == [5, 10, 20, 40, 60]


def test_attempt_increments_after_next_delay():
    """Each retry delay request should increment the attempt."""

    retry = RetryController(
        initial_delay=5,
        max_delay=60,
        max_attempts=5,
    )

    assert retry.attempt == 0

    retry.next_delay()
    assert retry.attempt == 1

    retry.next_delay()
    assert retry.attempt == 2


def test_max_delay_is_never_exceeded():
    """Retry delay should never exceed max_delay."""

    retry = RetryController(
        initial_delay=10,
        max_delay=25,
        max_attempts=10,
    )

    delays = [
        retry.next_delay(),
        retry.next_delay(),
        retry.next_delay(),
        retry.next_delay(),
    ]

    assert delays == [10, 20, 25, 25]


def test_retry_stops_after_max_attempts():
    """No more retries should be allowed after the limit."""

    retry = RetryController(
        initial_delay=5,
        max_delay=60,
        max_attempts=3,
    )

    retry.next_delay()
    retry.next_delay()
    retry.next_delay()

    assert retry.attempt == 3
    assert retry.can_retry() is False


def test_reset_restores_initial_state():
    """Reset should restore the controller to its initial state."""

    retry = RetryController(
        initial_delay=5,
        max_delay=60,
        max_attempts=5,
    )

    retry.next_delay()
    retry.next_delay()

    assert retry.attempt == 2

    retry.reset()

    assert retry.attempt == 0
    assert retry.can_retry() is True


def test_single_attempt_configuration():
    """A controller with one attempt should allow exactly one retry."""

    retry = RetryController(
        initial_delay=5,
        max_delay=60,
        max_attempts=1,
    )

    assert retry.can_retry() is True

    assert retry.next_delay() == 5
    assert retry.attempt == 1
    assert retry.can_retry() is False

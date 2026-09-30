from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryController:
    """Control retry delays using exponential backoff."""

    initial_delay: float
    max_delay: float
    max_attempts: int

    _attempt: int = 0

    @property
    def attempt(self) -> int:
        """Return the current retry attempt."""
        return self._attempt

    def can_retry(self) -> bool:
        """Return whether another retry attempt is allowed."""
        return self._attempt < self.max_attempts

    def next_delay(self) -> float:
        """Return the delay for the next retry attempt."""
        delay = min(
            self.initial_delay * (2**self._attempt),
            self.max_delay,
        )

        self._attempt += 1

        return delay

    def reset(self) -> None:
        """Reset the retry counter."""
        self._attempt = 0

"""Reusable backoff helper."""
from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def run_with_backoff(
    func: Callable[[], T],
    *,
    logger,
    attempts: int = 3,
    base_delay: float = 1.0,
) -> T:
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if attempt == attempts:
                logger.error(
                    "Operation failed after retries; manual intervention required",
                    exc_info=exc,
                    extra={"attempts": attempts, "manual_retry_required": True},
                )
                raise
            logger.warning(
                "Retrying operation after failure",
                exc_info=exc,
                extra={"attempt": attempt, "max_attempts": attempts},
            )
            delay = base_delay * (2 ** (attempt - 1))
            time.sleep(delay)
    raise last_exc  # pragma: no cover

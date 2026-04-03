"""Timing utility for measuring and logging operation durations."""

import time
from contextlib import contextmanager
from typing import Generator

from app.core.logging import logger


@contextmanager
def log_timer(operation: str) -> Generator[None, None, None]:
    """Context manager that logs the elapsed time of an operation.

    Usage:
        with log_timer("PDF parsing"):
            parse_pdf(file)
    """
    start = time.perf_counter()
    logger.info("Started: %s", operation)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("Completed: %s (%.2fs)", operation, elapsed)

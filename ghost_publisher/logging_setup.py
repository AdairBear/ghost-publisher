"""Logging setup — console plus a rotating file, so unattended runs leave evidence."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
MAX_BYTES = 1_000_000
BACKUP_COUNT = 5


def configure_logging(log_file: Path, *, verbose: bool = False) -> None:
    """Attach console and file handlers to the root logger.

    A file handler that cannot be created is reported on the console rather
    than swallowed — an unattended run with no log is a silent failure.

    Args:
        log_file: Destination log path; parent directories are created.
        verbose: Emit DEBUG rather than INFO on the console.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))
    root.addHandler(console)

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root.addHandler(file_handler)
    except OSError as exc:
        root.error(
            "could not open log file %s: %s (continuing, console only)", log_file, exc
        )

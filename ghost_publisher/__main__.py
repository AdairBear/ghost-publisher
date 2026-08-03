"""Allow `python -m ghost_publisher ...`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())

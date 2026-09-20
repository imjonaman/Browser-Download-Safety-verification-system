"""Download Security Agent — entry point."""

from __future__ import annotations

from agent.logging_config import setup_logging
from agent.native_messaging.host import run


def main() -> None:
    """Initialize logging and start the native messaging host."""
    setup_logging()
    run()


if __name__ == "__main__":
    main()

import logging

import pytest

from web_forager import cli


@pytest.fixture
def cli_logging():
    """Apply the CLI logging policy, then restore global logging state."""
    loggers = [logging.getLogger(name) for name in cli._DEPENDENCY_LOGGERS]
    levels = [logger.level for logger in loggers]
    yield cli._configure_logging
    for logger, level in zip(loggers, levels):
        logger.setLevel(level)
    for logger in (logging.getLogger(), logging.getLogger("fastmcp")):
        for handler in logger.handlers:
            handler.removeFilter(cli._REDACT_URLS)

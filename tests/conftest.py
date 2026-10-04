import logging

import pytest

from web_forager import cli


@pytest.fixture
def cli_logging():
    """Apply the CLI logging policy, then restore global logging state."""
    root = logging.getLogger()
    app = logging.getLogger(cli._APP_LOGGER)
    fastmcp = logging.getLogger(cli._FASTMCP_LOGGER)
    saved = (root.level, app.level, fastmcp.level, fastmcp.propagate)
    fastmcp_handlers = fastmcp.handlers[:]
    provider_levels = [
        (logging.getLogger(name), logging.getLogger(name).level)
        for name in cli._PROVIDER_LOGGERS
    ]
    yield cli._configure_logging
    root.setLevel(saved[0])
    app.setLevel(saved[1])
    fastmcp.setLevel(saved[2])
    fastmcp.propagate = saved[3]
    fastmcp.handlers[:] = fastmcp_handlers
    for provider, level in provider_levels:
        provider.setLevel(level)
    for handler in root.handlers:
        handler.removeFilter(cli._REDACT_URLS)

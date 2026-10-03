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
    yield cli._configure_logging
    root.setLevel(saved[0])
    app.setLevel(saved[1])
    fastmcp.setLevel(saved[2])
    fastmcp.propagate = saved[3]
    fastmcp.handlers[:] = fastmcp_handlers
    for handler in root.handlers:
        handler.removeFilter(cli._REDACT_URLS)

# Test assertions are the behavior under test, not production validation.
# ruff: noqa: S101

import asyncio
import importlib
import logging
from argparse import Namespace
from unittest.mock import Mock

from fastmcp import Client

from web_forager import cli
from web_forager.server import mcp


def test_server_registers_expected_tools_and_uses_stdio(monkeypatch) -> None:
    transports: list[str] = []

    def record_run(*, transport: str) -> None:
        transports.append(transport)

    monkeypatch.setattr(mcp, "run", record_run)

    assert cli._handle_serve(Namespace()) == 0

    tools = asyncio.run(mcp.list_tools())
    assert {tool.name for tool in tools} == {
        "duckduckgo_news_search",
        "duckduckgo_search",
        "search",
        "web_fetch",
    }
    assert transports == ["stdio"]


def test_search_alias_debug_logs_omit_query(monkeypatch, caplog, cli_logging) -> None:
    query = "FAKE_PRIVATE_QUERY alias"
    search = importlib.import_module("web_forager.duckduckgo_search")
    provider = Mock()
    provider.text.return_value = []
    monkeypatch.setattr(search, "DDGS", Mock(return_value=provider))
    monkeypatch.setattr(mcp, "run", lambda *, transport: None)
    caplog.set_level(logging.DEBUG)
    cli_logging(debug=True)
    assert cli._handle_serve(Namespace()) == 0

    async def check() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool("search", {"query": query})
            assert result.structured_content == {"result": []}

    asyncio.run(check())
    assert "Searching (max_results: 5" in caplog.text
    assert "Search returned no results" in caplog.text
    assert query not in caplog.text

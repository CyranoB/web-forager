# Test assertions are the behavior under test, not production validation.
# ruff: noqa: S101

import asyncio
from argparse import Namespace

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

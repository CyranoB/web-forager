import asyncio
import importlib
from unittest.mock import Mock

import pytest
from ddgs.exceptions import DDGSException
from fastmcp import Client
from fastmcp.exceptions import ToolError

from web_forager import SearchError, cli
from web_forager.server import mcp

news = importlib.import_module("web_forager.duckduckgo_news")
search = importlib.import_module("web_forager.duckduckgo_search")


@pytest.mark.parametrize(
    "module,function", [(news, "search_duckduckgo_news"), (search, "search_duckduckgo")]
)
def test_successful_empty_is_not_failure(monkeypatch, module, function):
    provider = Mock()
    provider.text.return_value = []
    provider.news.return_value = []
    monkeypatch.setattr(module, "DDGS", Mock(return_value=provider))
    assert getattr(module, function)("topic") == []


@pytest.mark.parametrize(
    "module,function", [(news, "search_duckduckgo_news"), (search, "search_duckduckgo")]
)
@pytest.mark.parametrize("error", [DDGSException("outage"), RuntimeError("unexpected")])
def test_failed_provider_is_not_empty(monkeypatch, module, function, error):
    monkeypatch.setattr(module, "DDGS", Mock(side_effect=error))
    invoke = getattr(module, function)
    with pytest.raises(SearchError):
        invoke("topic")


def test_web_fallback_can_recover(monkeypatch):
    execute = Mock(
        side_effect=[
            DDGSException("outage"),
            [{"title": "Result", "url": "https://example.com", "snippet": "text"}],
        ]
    )
    monkeypatch.setattr(search, "_execute_search", execute)
    assert search.search_duckduckgo("topic")[0]["title"] == "Result"
    assert execute.call_args.args[-1] == "brave"


def test_backend_failure_is_not_empty(monkeypatch):
    monkeypatch.setattr(
        search,
        "_execute_search",
        Mock(side_effect=DDGSException("backend unavailable")),
    )
    with pytest.raises(SearchError):
        search.search_duckduckgo("topic")


@pytest.mark.parametrize(
    "command,tool",
    [("news", "duckduckgo_news_search"), ("search", "duckduckgo_search")],
)
def test_cli_failure_and_empty_have_different_status(
    monkeypatch, command, tool, capsys
):
    args = cli._setup_parser().parse_args([command, "topic"])
    handler = getattr(cli, "_handle_" + command)
    monkeypatch.setattr(cli, tool, Mock(return_value=[]))
    assert handler(args) == 0
    assert capsys.readouterr().out.strip() == "[]"
    monkeypatch.setattr(cli, tool, Mock(side_effect=SearchError("Provider failed")))
    assert handler(args) == 1
    assert capsys.readouterr().out == ""


def test_mcp_surfaces_provider_failure(monkeypatch):
    monkeypatch.setattr(news, "DDGS", Mock(side_effect=DDGSException("outage")))

    async def check():
        async with Client(mcp) as client:
            with pytest.raises(ToolError, match="News search failed"):
                await client.call_tool("duckduckgo_news_search", {"query": "topic"})

    asyncio.run(check())

import asyncio
import importlib
import logging
from unittest.mock import Mock

import pytest
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
from fastmcp import Client
from fastmcp.exceptions import ToolError
from requests import HTTPError, Response

from web_forager import SearchError, cli
from web_forager.server import mcp

news = importlib.import_module("web_forager.duckduckgo_news")
search = importlib.import_module("web_forager.duckduckgo_search")


def http_failure(status):
    response = Response()
    response.status_code = status
    response.url = "https://example.com/private-query"
    return HTTPError("private provider details", response=response)


def mock_provider_failure(monkeypatch, module, error):
    provider = Mock()
    provider.text.side_effect = error
    provider.news.side_effect = error
    monkeypatch.setattr(module, "DDGS", Mock(return_value=provider))


FAILURES = [
    (
        TimeoutException("private provider details"),
        "timed out. Try again or use another search tool.",
    ),
    (
        RatelimitException("private provider details"),
        "rate limited. Wait before trying again or use another search tool.",
    ),
    (
        http_failure(503),
        "backend unavailable. Try again later or use another search tool.",
    ),
    (
        DDGSException("backend timed out private provider details"),
        "failed. Try another search tool; coverage is incomplete.",
    ),
]


@pytest.mark.parametrize(
    "module,function,prefix",
    [
        (news, "search_duckduckgo_news", "News search"),
        (search, "search_duckduckgo", "Search"),
    ],
)
@pytest.mark.parametrize("wrapper", ["argument", "cause"])
@pytest.mark.parametrize("inner,diagnostic", FAILURES)
def test_wrapped_provider_evidence_is_preserved(
    monkeypatch, module, function, prefix, wrapper, inner, diagnostic
):
    if wrapper == "argument":
        # ddgs aggregates engine failures as DDGSException(original_exception).
        error = DDGSException(inner)
    else:
        error = DDGSException("private wrapper details")
        error.__cause__ = inner
    mock_provider_failure(monkeypatch, module, error)
    with pytest.raises(SearchError) as failure:
        getattr(module, function)("private topic")
    assert str(failure.value) == f"{prefix} {diagnostic}"


@pytest.mark.parametrize(
    "module,function,prefix",
    [
        (news, "search_duckduckgo_news", "News search"),
        (search, "search_duckduckgo", "Search"),
    ],
)
@pytest.mark.parametrize(
    "error,diagnostic",
    [
        (http_failure(408), "timed out. Try again or use another search tool."),
        (
            http_failure(429),
            "rate limited. Wait before trying again or use another search tool.",
        ),
        (
            http_failure(502),
            "backend unavailable. Try again later or use another search tool.",
        ),
        (
            http_failure(503),
            "backend unavailable. Try again later or use another search tool.",
        ),
        (http_failure(504), "timed out. Try again or use another search tool."),
        (http_failure(403), "failed. Try another search tool; coverage is incomplete."),
        (
            TimeoutException("private query and URL"),
            "timed out. Try again or use another search tool.",
        ),
        (
            RatelimitException("private query and URL"),
            "rate limited. Wait before trying again or use another search tool.",
        ),
    ],
)
def test_provider_failure_has_action(
    monkeypatch, module, function, prefix, error, diagnostic
):
    mock_provider_failure(monkeypatch, module, error)
    with pytest.raises(SearchError) as failure:
        getattr(module, function)("private topic")
    assert str(failure.value) == f"{prefix} {diagnostic}"


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


@pytest.mark.parametrize(
    "error_type", [DDGSException, TimeoutException, RatelimitException]
)
@pytest.mark.parametrize("empty", [False, True])
def test_web_fallback_can_recover(monkeypatch, error_type, empty):
    results = (
        []
        if empty
        else [{"title": "Result", "href": "https://example.com", "body": "text"}]
    )
    provider = Mock()
    provider.text.side_effect = [error_type("backend outage"), results]
    monkeypatch.setattr(search, "DDGS", Mock(return_value=provider))
    assert search.search_duckduckgo("topic") == (
        []
        if empty
        else [{"title": "Result", "url": "https://example.com", "snippet": "text"}]
    )


@pytest.mark.parametrize(
    "module,function,prefix",
    [
        (news, "search_duckduckgo_news", "News search"),
        (search, "search_duckduckgo", "Search"),
    ],
)
@pytest.mark.parametrize("error_type", [DDGSException, RuntimeError, HTTPError])
def test_error_text_is_not_evidence(monkeypatch, module, function, prefix, error_type):
    error = error_type(
        "timed out; rate limited 429; backend unavailable 503; private query"
    )
    monkeypatch.setattr(module, "DDGS", Mock(side_effect=error))
    with pytest.raises(SearchError) as failure:
        getattr(module, function)("private topic")
    assert str(failure.value) == (
        f"{prefix} failed. Try another search tool; coverage is incomplete."
    )


@pytest.mark.parametrize(
    "final_error,diagnostic",
    [
        (
            RatelimitException("private details"),
            "Search rate limited. Wait before trying again or use another search tool.",
        ),
        (
            RuntimeError("backend timed out"),
            "Search failed. Try another search tool; coverage is incomplete.",
        ),
    ],
)
def test_failed_fallback_reports_final_provider_evidence(
    monkeypatch, final_error, diagnostic
):
    provider = Mock()
    provider.text.side_effect = [TimeoutException("private details"), final_error]
    monkeypatch.setattr(search, "DDGS", Mock(return_value=provider))
    with pytest.raises(SearchError) as failure:
        search.search_duckduckgo("private topic")
    assert str(failure.value) == diagnostic


@pytest.mark.parametrize(
    "command,module",
    [("news", news), ("search", search)],
)
def test_cli_failure_and_empty_have_different_status(
    monkeypatch, command, module, capsys
):
    provider = Mock()
    provider.text.return_value = []
    provider.news.return_value = []
    monkeypatch.setattr(module, "DDGS", Mock(return_value=provider))
    monkeypatch.setattr("sys.argv", ["web-forager", command, "topic"])
    assert cli.main() == 0
    assert capsys.readouterr().out.strip() == "[]"
    provider.text.side_effect = DDGSException("outage")
    provider.news.side_effect = DDGSException("outage")
    assert cli.main() == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "module,tool,prefix",
    [
        (news, "duckduckgo_news_search", "News search"),
        (search, "duckduckgo_search", "Search"),
    ],
)
@pytest.mark.parametrize("error,diagnostic", FAILURES)
@pytest.mark.parametrize("output_format", ["json", "text"])
def test_mcp_surfaces_safe_provider_failure(
    monkeypatch, module, tool, prefix, error, diagnostic, output_format, caplog
):
    monkeypatch.setattr(module, "DDGS", Mock(side_effect=error))

    async def check():
        async with Client(mcp) as client:
            with pytest.raises(ToolError) as failure:
                await client.call_tool(
                    tool, {"query": "private topic", "output_format": output_format}
                )
            assert f"{prefix} {diagnostic}" in str(failure.value)
            assert "private" not in str(failure.value)

    asyncio.run(check())
    assert "private provider details" not in caplog.text
    assert "https://example.com/private-query" not in caplog.text
    assert "private topic" not in caplog.text


@pytest.mark.parametrize(
    "command,module,prefix",
    [("news", news, "News search"), ("search", search, "Search")],
)
@pytest.mark.parametrize("error,diagnostic", FAILURES)
@pytest.mark.parametrize("output_format", ["json", "text"])
def test_cli_reports_safe_provider_cause(
    monkeypatch,
    command,
    module,
    prefix,
    error,
    diagnostic,
    output_format,
    capsys,
    caplog,
):
    private = "private-topic https://example.com/private?token=secret-value"
    mock_provider_failure(monkeypatch, module, error)
    monkeypatch.setattr(
        "sys.argv", ["web-forager", command, private, "--output-format", output_format]
    )
    with caplog.at_level(logging.DEBUG):
        assert cli.main() == 1
    assert capsys.readouterr().out == ""
    assert f"{prefix} {diagnostic}" in caplog.text
    assert private not in caplog.text
    assert "secret-value" not in caplog.text
    assert "private provider details" not in caplog.text
    assert "https://example.com/private-query" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.parametrize("command", ["search", "news"])
def test_cli_suppresses_private_dependency_logs(monkeypatch, command, capsys, caplog):
    from ddgs.ddgs import DDGS

    private = "https://example.com/private?token=private-value"

    def failed_request(*args, **kwargs):
        # Exercise actual ddgs aggregation, which also logs raw engine exceptions.
        for name in ("primp", "httpx", "httpcore", "ddgs.engines.yahoo_news"):
            logging.getLogger(name).warning("Provider details: %s", private)
        raise DDGSException(HTTPError(private))

    engine = Mock(provider="provider", name="provider")
    engine.search.side_effect = failed_request
    monkeypatch.setattr(DDGS, "_get_engines", Mock(return_value=[engine]))
    monkeypatch.setattr("sys.argv", ["web-forager", command, "private topic"])
    # Isolate logging configuration changes made by the CLI from other tests.
    for name in ("ddgs", "primp", "httpx", "httpcore"):
        monkeypatch.setattr(logging.getLogger(name), "level", logging.NOTSET)
    with caplog.at_level(logging.DEBUG):
        assert cli.main() == 1
    assert capsys.readouterr().out == ""
    assert "failed. Try another search tool" in caplog.text
    assert "private" not in caplog.text

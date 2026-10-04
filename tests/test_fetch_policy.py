import asyncio
import importlib
import logging
import socket
from unittest.mock import Mock

import pytest
import requests
import urllib3

from web_forager import cli

fetch = importlib.import_module("web_forager.web_fetch")
PUBLIC = "https://www.example.com/article"
SECRET = "FAKE_PRIVATE_TOKEN"


def response(text="", status=200, location=None):
    result = requests.Response()
    result.status_code = status
    result._content = text.encode()
    result._content_consumed = True
    if location:
        result.headers["Location"] = location
    return result


@pytest.fixture
def public_dns(monkeypatch):
    lookup = Mock(
        return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
    )
    monkeypatch.setattr(fetch.socket, "getaddrinfo", lookup)
    return lookup


@pytest.mark.parametrize(
    "url",
    [
        f"{PUBLIC}?token={SECRET}",
        f"{PUBLIC}?",
        f"{PUBLIC}#{SECRET}",
        f"https://user:{SECRET}@www.example.com/article",
        "http://localhost/a",
        "http://intranet/a",
        "http://service.internal/a",
        "http://service.local/a",
        "http://[fe80::1%25en0]/a",
    ],
)
def test_ineligible_urls_never_forward(monkeypatch, public_dns, url):
    direct = Mock(return_value=fetch._DirectResult(None, [url]))
    proxy = Mock()
    monkeypatch.setattr(fetch, "_direct_fetch", direct)
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    with pytest.raises(RuntimeError, match="ineligible"):
        fetch.fetch_url(url)
    proxy.assert_not_called()


@pytest.mark.parametrize(
    "addresses",
    [
        [],
        ["127.0.0.1"],
        ["10.0.0.1"],
        ["::1"],
        ["169.254.169.254"],
        ["93.184.216.34", "192.168.0.1"],
    ],
)
def test_nonpublic_or_mixed_dns_is_direct_only(monkeypatch, addresses):
    monkeypatch.setattr(
        fetch.socket,
        "getaddrinfo",
        lambda *a, **kw: [(2, 1, 6, "", (ip, 443)) for ip in addresses],
    )
    assert not fetch._can_forward(PUBLIC)


def test_unresolved_dns_is_direct_only(monkeypatch):
    monkeypatch.setattr(
        fetch.socket, "getaddrinfo", Mock(side_effect=socket.gaierror())
    )
    assert not fetch._can_forward(PUBLIC)


def test_public_fallback_and_direct_only(monkeypatch, public_dns):
    monkeypatch.setattr(
        fetch, "_direct_fetch", lambda *a: fetch._DirectResult(None, [PUBLIC])
    )
    proxy = Mock(return_value="reader content")
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    assert fetch.fetch_url(PUBLIC) == "reader content"
    proxy.reset_mock()
    with pytest.raises(RuntimeError, match="disabled"):
        fetch.fetch_url(PUBLIC, allow_jina=False)
    proxy.assert_not_called()
    assert fetch.jina_fetch is fetch.web_fetch


@pytest.mark.parametrize(
    "first,second",
    [(PUBLIC, PUBLIC + "?token=" + SECRET), (PUBLIC + "?token=" + SECRET, PUBLIC)],
)
def test_redirects_cannot_launder_sensitive_urls(
    monkeypatch, public_dns, first, second
):
    get = Mock(
        side_effect=[response(status=302, location=second), requests.Timeout(SECRET)]
    )
    monkeypatch.setattr(fetch.requests, "get", get)
    proxy = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    with pytest.raises(RuntimeError, match="ineligible"):
        fetch.fetch_url(first)
    assert get.call_count == 2
    assert all(call.kwargs["allow_redirects"] is False for call in get.call_args_list)
    proxy.assert_not_called()


def test_public_redirect_can_fall_back(monkeypatch, public_dns):
    monkeypatch.setattr(
        fetch.requests,
        "get",
        Mock(side_effect=[response(status=302, location="/next"), requests.Timeout()]),
    )
    monkeypatch.setattr(fetch, "_jina_fetch", Mock(return_value="read"))
    assert fetch.fetch_url(PUBLIC) == "read"


def test_redirect_limit_fails_closed(monkeypatch, public_dns):
    monkeypatch.setattr(
        fetch.requests, "get", lambda *a, **kw: response(status=302, location=PUBLIC)
    )
    proxy = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    with pytest.raises(RuntimeError, match="disabled"):
        fetch.fetch_url(PUBLIC)
    proxy.assert_not_called()


def test_errors_and_logs_do_not_disclose_urls(monkeypatch, caplog, public_dns):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(
        fetch.requests, "get", Mock(side_effect=requests.Timeout(SECRET))
    )
    with pytest.raises(RuntimeError) as failure:
        fetch.fetch_url(PUBLIC + "?token=" + SECRET)
    assert SECRET not in str(failure.value) + caplog.text
    with pytest.raises(RuntimeError) as failure:
        fetch.fetch_url(PUBLIC)
    assert SECRET not in str(failure.value) + caplog.text
    assert failure.value.__suppress_context__


def test_debug_server_logs_omit_signed_url(monkeypatch, caplog, cli_logging):
    """Run the real Requests/urllib3 path over a fake connection with debug on."""
    from fastmcp import Client

    signed = f"http://www.example.com/report?X-Amz-Signature={SECRET}"
    body = ARTICLE.encode()

    def fake_connection(self):
        client, server = socket.socketpair()
        server.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
            + f"Content-Length: {len(body)}\r\n\r\n".encode()
            + body
        )
        self._fake_server = server
        return client

    for name in ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(urllib3.connection.HTTPConnection, "_new_conn", fake_connection)
    proxy = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    caplog.set_level(logging.DEBUG)
    cli_logging(debug=True)
    logging.getLogger("urllib3").warning("Failed to parse headers (url=%s)", signed)

    async def check():
        async with Client(fetch.mcp) as client:
            result = await client.call_tool(
                "web_fetch", {"url": signed, "allow_jina": False}
            )
            assert "0123456789" in result.data

    asyncio.run(check())
    proxy.assert_not_called()
    assert "Direct fetch successful" in caplog.text
    assert "<redacted URL>" in caplog.text
    assert SECRET not in caplog.text


def test_logged_urls_and_tracebacks_are_redacted(caplog, cli_logging):
    caplog.set_level(logging.DEBUG)
    cli_logging(debug=True)
    app = logging.getLogger("web_forager.test")
    app.warning("Max retries exceeded with url: /report?sig=%s", SECRET)
    try:
        raise requests.ConnectionError(f"https://www.example.com/r?sig={SECRET}")
    except requests.ConnectionError:
        app.exception("Request failed")
    assert "Request failed" in caplog.text
    assert "Max retries exceeded with url: <redacted URL>" in caplog.text
    assert SECRET not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


def test_successful_preview_extraction_does_not_prove_completeness(monkeypatch):
    html = (
        "<article><h1>Report</h1><p>"
        + ("Preview of the report. " * 20)
        + "</p><p>Subscribe to read the complete report.</p></article>"
    )
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **kw: response(html))
    result = fetch.fetch_url(PUBLIC, allow_jina=False)
    assert "Subscribe" in result


def test_successful_direct_fetch_preserves_format_and_skips_proxy(monkeypatch):
    monkeypatch.setattr(
        fetch.requests,
        "get",
        lambda *a, **kw: response(
            "<html><body><article><h1>Evidence</h1><p>"
            + "Evidence. " * 40
            + "</p></article></body></html>"
        ),
    )
    proxy = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    result = fetch.web_fetch(PUBLIC, format="json")
    assert set(result) == {"url", "title", "content"}
    assert result["url"] == PUBLIC
    proxy.assert_not_called()


ARTICLE = (
    "<html><body><article><p>" + "0123456789" * 30 + "</p></article></body></html>"
)


def direct_article(monkeypatch):
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **kw: response(ARTICLE))
    monkeypatch.setattr(fetch, "_jina_fetch", Mock())
    return fetch.fetch_url(PUBLIC)


def test_paged_markdown_reports_next_offset(monkeypatch):
    full = direct_article(monkeypatch)
    first = fetch.web_fetch(PUBLIC, max_length=120)
    assert first == (
        f"{full[:120]}\n\n[Truncated: characters 0-120 of {len(full)} (direct). "
        "Continue with offset=120.]"
    )
    last = fetch.web_fetch(PUBLIC, max_length=len(full), offset=120)
    assert last == (
        f"{full[120:]}\n\n[End of content: characters 120-{len(full)} "
        f"of {len(full)} (direct).]"
    )
    assert fetch.web_fetch(PUBLIC, offset=None) == full


def test_paged_json_reports_pagination_fields(monkeypatch):
    full = direct_article(monkeypatch)
    page = fetch.web_fetch(PUBLIC, format="json", max_length=50, offset=100)
    assert page["content"] == full[100:150]
    assert (
        page["source"],
        page["offset"],
        page["total_length"],
        page["next_offset"],
    ) == ("direct", 100, len(full), 150)
    rest = fetch.web_fetch(PUBLIC, format="json", offset=150)
    assert rest["content"] == full[150:]
    assert rest["next_offset"] is None


def test_offset_beyond_content_is_reported(monkeypatch):
    full = direct_article(monkeypatch)
    with pytest.raises(ValueError, match=f"beyond the content length \\({len(full)}"):
        fetch.web_fetch(PUBLIC, offset=len(full))


@pytest.mark.parametrize(
    "kwargs",
    [{"offset": -1}, {"offset": "x"}, {"offset": True}, {"max_length": 0}],
)
def test_invalid_pagination_fails_before_fetching(monkeypatch, kwargs):
    get = Mock()
    monkeypatch.setattr(fetch.requests, "get", get)
    with pytest.raises(ValueError):
        fetch.web_fetch(PUBLIC, **kwargs)
    get.assert_not_called()


def test_jina_fallback_is_paged(monkeypatch, public_dns):
    monkeypatch.setattr(
        fetch, "_direct_fetch", Mock(return_value=fetch._DirectResult(None, [PUBLIC]))
    )
    monkeypatch.setattr(fetch, "_jina_fetch", Mock(return_value="abcdefghij"))
    assert fetch.fetch_url(PUBLIC, max_length=4, offset=4) == (
        "efgh\n\n[Truncated: characters 4-8 of 10 (jina). Continue with offset=8.]"
    )


def jina_json(monkeypatch, public_dns, document):
    monkeypatch.setattr(
        fetch, "_direct_fetch", Mock(return_value=fetch._DirectResult(None, [PUBLIC]))
    )
    monkeypatch.setattr(fetch, "_jina_fetch", Mock(return_value=document))


def test_jina_json_pages_nested_content(monkeypatch, public_dns):
    document = {"code": 200, "data": {"title": "T", "content": "abcdefghij"}}
    jina_json(monkeypatch, public_dns, document)
    page = fetch.fetch_url(PUBLIC, output_format="json", max_length=4, offset=4)
    assert page["data"] == {"title": "T", "content": "efgh"}
    assert (page["source"], page["total_length"], page["next_offset"]) == (
        "jina",
        10,
        8,
    )
    assert document["data"]["content"] == "abcdefghij"
    with pytest.raises(ValueError, match="beyond the content length"):
        fetch.fetch_url(PUBLIC, output_format="json", offset=10)


def test_jina_json_without_text_cannot_be_paged(monkeypatch, public_dns):
    jina_json(monkeypatch, public_dns, {"code": 200, "data": {"title": "T"}})
    assert fetch.fetch_url(PUBLIC, output_format="json") == {
        "code": 200,
        "data": {"title": "T"},
    }
    with pytest.raises(ValueError, match="no text content"):
        fetch.fetch_url(PUBLIC, output_format="json", max_length=4)


def test_mcp_schema_rejects_boolean_offset(monkeypatch):
    from fastmcp import Client
    from fastmcp.exceptions import ToolError

    monkeypatch.setattr(fetch, "fetch_url", lambda *a, **kw: f"offset={kw['offset']}")

    async def check():
        async with Client(fetch.mcp) as client:
            with pytest.raises(ToolError, match="validation error"):
                await client.call_tool("web_fetch", {"url": PUBLIC, "offset": True})
            result = await client.call_tool(
                "web_fetch", {"url": PUBLIC, "offset": None}
            )
            assert result.data == "offset=0"

    asyncio.run(check())


def test_cli_direct_only(monkeypatch):
    invoke = Mock(return_value="content")
    monkeypatch.setattr(cli, "fetch_url", invoke)
    args = cli._setup_parser().parse_args(["fetch", PUBLIC, "--direct-only"])
    assert cli._handle_fetch(args) == 0
    assert invoke.call_args.kwargs["allow_jina"] is False
    assert invoke.call_args.kwargs["offset"] == 0


def test_cli_fetch_offset(monkeypatch):
    invoke = Mock(return_value="content")
    monkeypatch.setattr(cli, "fetch_url", invoke)
    args = cli._setup_parser().parse_args(
        ["fetch", PUBLIC, "--max-length", "100", "--offset", "200"]
    )
    assert cli._handle_fetch(args) == 0
    assert invoke.call_args.kwargs["max_length"] == 100
    assert invoke.call_args.kwargs["offset"] == 200


def test_cli_fetch_failure(monkeypatch, caplog):
    monkeypatch.setattr(
        cli, "fetch_url", Mock(side_effect=RuntimeError("Direct fetch failed"))
    )
    args = cli._setup_parser().parse_args(["fetch", PUBLIC + "?token=" + SECRET])
    assert cli._handle_fetch(args) == 1
    assert SECRET not in caplog.text


def extraction_error(monkeypatch, *pages, extractor="extract"):
    """Serve pages over HTTP, then make trafilatura fail on the retrieved HTML."""
    get = Mock(side_effect=list(pages))
    monkeypatch.setattr(fetch.requests, "get", get)
    monkeypatch.setattr(
        fetch.trafilatura, extractor, Mock(side_effect=RuntimeError(SECRET))
    )
    return get


@pytest.mark.parametrize(
    "output_format,reader",
    [
        ("markdown", "reader content"),
        ("json", {"data": {"content": "reader content"}}),
    ],
)
def test_extraction_failure_falls_back_for_public_url(
    monkeypatch, caplog, public_dns, output_format, reader
):
    caplog.set_level(logging.DEBUG)
    extraction_error(monkeypatch, response(ARTICLE))
    proxy = Mock(return_value=reader)
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    assert fetch.fetch_url(PUBLIC, output_format=output_format) == reader
    proxy.assert_called_once_with(PUBLIC, output_format, False)
    assert "Direct content extraction failed" in caplog.text
    assert SECRET not in caplog.text


def test_metadata_failure_keeps_direct_content(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    extraction_error(monkeypatch, response(ARTICLE), extractor="bare_extraction")
    proxy = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    result = fetch.fetch_url(PUBLIC, output_format="json")
    assert (result["url"], result["title"]) == (PUBLIC, "")
    assert "0123456789" in result["content"]
    proxy.assert_not_called()
    assert SECRET not in caplog.text


def test_extraction_failure_fallback_is_paged(monkeypatch, public_dns):
    extraction_error(monkeypatch, response(ARTICLE))
    monkeypatch.setattr(fetch, "_jina_fetch", Mock(return_value="abcdefghij"))
    assert fetch.fetch_url(PUBLIC, max_length=4) == (
        "abcd\n\n[Truncated: characters 0-4 of 10 (jina). Continue with offset=4.]"
    )


def test_extraction_failure_after_public_redirect_falls_back(monkeypatch, public_dns):
    get = extraction_error(
        monkeypatch, response(status=302, location="/next"), response(ARTICLE)
    )
    monkeypatch.setattr(fetch, "_jina_fetch", Mock(return_value="read"))
    assert fetch.fetch_url(PUBLIC) == "read"
    assert get.call_args.args[0] == "https://www.example.com/next"
    assert public_dns.call_count == 2


@pytest.mark.parametrize(
    "first,pages",
    [
        (PUBLIC, [response(status=302, location=f"/next?token={SECRET}")]),
        (f"{PUBLIC}?token={SECRET}", [response(status=302, location=PUBLIC)]),
        (f"{PUBLIC}?token={SECRET}", []),
        ("http://service.internal/a", []),
    ],
)
def test_extraction_failure_never_forwards_ineligible_chain(
    monkeypatch, caplog, public_dns, first, pages
):
    caplog.set_level(logging.DEBUG)
    extraction_error(monkeypatch, *pages, response(ARTICLE))
    proxy = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    with pytest.raises(RuntimeError, match="ineligible") as failure:
        fetch.fetch_url(first)
    assert SECRET not in str(failure.value) + caplog.text
    proxy.assert_not_called()


def test_extraction_failure_respects_direct_only(monkeypatch, public_dns):
    extraction_error(monkeypatch, response(ARTICLE))
    proxy = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", proxy)
    with pytest.raises(RuntimeError, match="disabled"):
        fetch.fetch_url(PUBLIC, allow_jina=False)
    proxy.assert_not_called()
    public_dns.assert_not_called()


def test_extraction_and_fallback_failure_is_sanitized(monkeypatch, caplog, public_dns):
    caplog.set_level(logging.DEBUG)
    extraction_error(monkeypatch, response(ARTICLE), response(status=503))
    with pytest.raises(RuntimeError, match="Jina Reader failed") as failure:
        fetch.fetch_url(PUBLIC)
    assert SECRET not in str(failure.value) + caplog.text
    assert failure.value.__suppress_context__


def test_extraction_failure_recovers_through_cli_and_mcp(
    monkeypatch, public_dns, capsys
):
    from fastmcp import Client

    extraction_error(monkeypatch, response(ARTICLE), response(ARTICLE))
    monkeypatch.setattr(fetch, "_jina_fetch", Mock(return_value="reader content"))
    args = cli._setup_parser().parse_args(["fetch", PUBLIC])
    assert cli._handle_fetch(args) == 0
    assert capsys.readouterr().out.strip() == "reader content"

    async def check():
        async with Client(fetch.mcp) as client:
            result = await client.call_tool("web_fetch", {"url": PUBLIC})
            assert result.data == "reader content"

    asyncio.run(check())

import importlib
import logging
import socket
from unittest.mock import Mock

import pytest
import requests

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
    result = fetch.web_fetch(PUBLIC, format="json", max_length=20)
    assert set(result) == {"url", "title", "content"}
    assert result["url"] == PUBLIC
    assert result["content"].endswith("... (content truncated)")
    proxy.assert_not_called()


def test_cli_direct_only(monkeypatch):
    invoke = Mock(return_value="content")
    monkeypatch.setattr(cli, "fetch_url", invoke)
    args = cli._setup_parser().parse_args(["fetch", PUBLIC, "--direct-only"])
    assert cli._handle_fetch(args) == 0
    assert invoke.call_args.kwargs["allow_jina"] is False


def test_cli_fetch_failure(monkeypatch, caplog):
    monkeypatch.setattr(
        cli, "fetch_url", Mock(side_effect=RuntimeError("Direct fetch failed"))
    )
    args = cli._setup_parser().parse_args(["fetch", PUBLIC + "?token=" + SECRET])
    assert cli._handle_fetch(args) == 1
    assert SECRET not in caplog.text

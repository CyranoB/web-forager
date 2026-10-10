# Test assertions are the behavior under test, not production validation.
# ruff: noqa: S101

import asyncio
import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from fastmcp import Client

from web_forager import cli
from web_forager import youtube_transcript as youtube

fetch = importlib.import_module("web_forager.web_fetch")
VIDEO_ID = "dQw4w9WgXcQ"
WATCH_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}&t=5"
CANONICAL_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


@pytest.mark.parametrize(
    "url",
    [
        WATCH_URL,
        f"https://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?si=tracking",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}",
    ],
)
def test_video_urls_are_recognized(url):
    assert youtube.video_id_from_url(url) == VIDEO_ID


@pytest.mark.parametrize(
    "url",
    [
        f"https://youtube.com.evil.test/watch?v={VIDEO_ID}",
        f"https://example.com/?next=https://youtube.com/watch?v={VIDEO_ID}",
        "https://www.youtube.com/@creator",
    ],
)
def test_other_urls_are_not_transcripts(url):
    assert youtube.video_id_from_url(url) is None


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=invalid",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&v=abcdefghijk",
        f"https://user:secret@www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}/unexpected",
    ],
)
def test_invalid_video_urls_fail_closed(url):
    with pytest.raises(ValueError, match="valid YouTube video URL"):
        youtube.video_id_from_url(url)


@pytest.fixture
def captions(monkeypatch):
    snippets = [
        SimpleNamespace(start=0.0, text="Hello  world"),
        SimpleNamespace(start=62.9, text="Next line"),
    ]

    class Fetched(list):
        language = "English"
        language_code = "en"
        is_generated = True

    selected = Mock()
    selected.fetch.return_value = Fetched(snippets)
    available = Mock()
    available.find_transcript.return_value = selected
    provider = Mock()
    provider.list.return_value = available
    monkeypatch.setattr(
        youtube.ytt, "YouTubeTranscriptApi", Mock(return_value=provider)
    )
    return provider, available, selected


def test_fetch_youtube_returns_timestamped_content_without_page_fallback(
    monkeypatch, captions
):
    direct = Mock()
    jina = Mock()
    monkeypatch.setattr(fetch, "_direct_fetch", direct)
    monkeypatch.setattr(fetch, "_jina_fetch", jina)

    markdown = fetch.fetch_url(WATCH_URL, allow_jina=False, with_images=True)
    assert markdown == (
        f"YouTube transcript: {CANONICAL_URL}\n"
        "Language: English (en); captions: automatic\n\n"
        "[00:00:00] Hello world\n[00:01:02] Next line"
    )
    direct.assert_not_called()
    jina.assert_not_called()
    provider, available, selected = captions
    provider.list.assert_called_once_with(VIDEO_ID)
    available.find_transcript.assert_called_once_with(["en"])
    selected.fetch.assert_called_once_with()


def test_json_transcript_paging_and_metadata(captions):
    whole = fetch.fetch_url(WATCH_URL, output_format="json")
    assert whole == {
        "url": CANONICAL_URL,
        "video_id": VIDEO_ID,
        "language": "English",
        "language_code": "en",
        "is_generated": True,
        "content": "[00:00:00] Hello world\n[00:01:02] Next line",
    }
    part = fetch.fetch_url(WATCH_URL, output_format="json", max_length=12)
    assert part["content"] == whole["content"][:12]
    assert part["source"] == "youtube"
    assert part["next_offset"] == 12
    assert part["language_code"] == "en"
    rest = fetch.fetch_url(WATCH_URL, output_format="json", offset=12)
    assert part["content"] + rest["content"] == whole["content"]


def test_default_language_uses_an_available_track(captions):
    from youtube_transcript_api import NoTranscriptFound

    _, available, selected = captions
    available.find_transcript.side_effect = NoTranscriptFound(
        VIDEO_ID, ["en"], available
    )
    available.__iter__ = Mock(return_value=iter([selected]))
    selected.fetch.return_value.language = "French"
    selected.fetch.return_value.language_code = "fr"

    result = fetch.fetch_url(WATCH_URL, output_format="json")
    assert result["language_code"] == "fr"
    selected.fetch.assert_called_once_with()


def test_requested_language_is_reported_when_unavailable(captions):
    from youtube_transcript_api import NoTranscriptFound

    _, available, selected = captions
    available.find_transcript.side_effect = NoTranscriptFound(
        VIDEO_ID, ["fr"], available
    )
    with pytest.raises(RuntimeError, match="Requested caption language is unavailable"):
        fetch.fetch_url(WATCH_URL, language="fr")
    selected.fetch.assert_not_called()


def test_caption_failures_never_fall_back_or_leak_url(monkeypatch, caplog):
    from youtube_transcript_api import TranscriptsDisabled

    provider = Mock()
    provider.list.side_effect = TranscriptsDisabled(VIDEO_ID)
    monkeypatch.setattr(
        youtube.ytt, "YouTubeTranscriptApi", Mock(return_value=provider)
    )
    jina = Mock()
    monkeypatch.setattr(fetch, "_jina_fetch", jina)

    with pytest.raises(RuntimeError, match="No accessible captions") as failure:
        fetch.fetch_url(WATCH_URL + "&token=PRIVATE")
    assert "PRIVATE" not in str(failure.value) + caplog.text
    jina.assert_not_called()


def test_blocked_caption_fetch_is_reported_without_provider_details(monkeypatch):
    from youtube_transcript_api import IpBlocked

    provider = Mock()
    provider.list.side_effect = IpBlocked(VIDEO_ID)
    monkeypatch.setattr(
        youtube.ytt, "YouTubeTranscriptApi", Mock(return_value=provider)
    )

    with pytest.raises(RuntimeError, match="blocked transcript access") as failure:
        fetch.fetch_url(WATCH_URL)
    assert failure.value.__suppress_context__


def test_provider_requests_have_a_timeout(monkeypatch):
    request = Mock(return_value=Mock())
    monkeypatch.setattr(requests.Session, "request", request)
    youtube._TimedSession().get(CANONICAL_URL)
    assert request.call_args.kwargs["timeout"] == 15


def test_provider_network_errors_are_sanitized(monkeypatch):
    provider = Mock()
    provider.list.side_effect = requests.Timeout("PRIVATE")
    monkeypatch.setattr(
        youtube.ytt, "YouTubeTranscriptApi", Mock(return_value=provider)
    )
    with pytest.raises(
        RuntimeError, match="YouTube transcript is unavailable"
    ) as failure:
        fetch.fetch_url(WATCH_URL)
    assert "PRIVATE" not in str(failure.value)
    assert failure.value.__suppress_context__


def test_cli_and_mcp_share_youtube_fetch(captions, capsys):
    args = cli._setup_parser().parse_args(
        ["fetch", WATCH_URL, "--format", "json", "--language", "fr"]
    )
    assert cli._handle_fetch(args) == 0
    assert '"video_id": "dQw4w9WgXcQ"' in capsys.readouterr().out
    assert captions[1].find_transcript.call_args.args == (["fr"],)

    async def check():
        async with Client(fetch.mcp) as client:
            result = await client.call_tool("web_fetch", {"url": WATCH_URL})
            assert "[00:01:02] Next line" in result.data

    asyncio.run(check())

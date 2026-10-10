"""Retrieve caption text from public YouTube video URLs."""

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
import youtube_transcript_api as ytt

_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "www.youtube-nocookie.com",
    "youtube-nocookie.com",
    "youtu.be",
    "www.youtu.be",
}
_REQUEST_TIMEOUT = 15


class _TimedSession(requests.Session):
    """Bound the provider's HTTP calls so a fetch cannot wait indefinitely."""

    def request(
        self, method: str, url: str | bytes, *args: Any, **kwargs: Any
    ) -> requests.Response:
        kwargs.setdefault("timeout", _REQUEST_TIMEOUT)
        return super().request(method, url, *args, **kwargs)


def video_id_from_url(url: str) -> str | None:
    """Return a video ID for supported YouTube URLs, or None for other pages."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if host not in _YOUTUBE_HOSTS:
        return None

    path = parsed.path.strip("/").split("/")
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = path[0] if len(path) == 1 else None
    elif path == ["watch"]:
        ids = parse_qs(parsed.query).get("v", [])
        candidate = ids[0] if len(ids) == 1 else None
    elif len(path) == 2 and path[0] in {"shorts", "live", "embed"}:
        candidate = path[1]
    else:
        return None

    if parsed.username is not None or parsed.password is not None:
        raise ValueError("A valid YouTube video URL is required")
    if parsed.port not in (None, 80, 443):
        raise ValueError("A valid YouTube video URL is required")
    if not candidate or not _VIDEO_ID.fullmatch(candidate):
        raise ValueError("A valid YouTube video URL is required")
    return candidate


def fetch_transcript(
    video_id: str, output_format: str, language: str | None = None
) -> str | dict[str, object]:
    """Return timestamped captions and metadata without exposing provider errors."""
    try:
        available = ytt.YouTubeTranscriptApi(http_client=_TimedSession()).list(video_id)
        if language is not None:
            selected = available.find_transcript([language])
        else:
            try:
                selected = available.find_transcript(["en"])
            except ytt.NoTranscriptFound:
                try:
                    selected = next(iter(available))
                except StopIteration:
                    raise RuntimeError(
                        "No accessible captions are available for this YouTube video"
                    ) from None
        transcript = selected.fetch()
    except ytt.NoTranscriptFound:
        message = (
            "Requested caption language is unavailable"
            if language
            else "No accessible captions are available for this YouTube video"
        )
        raise RuntimeError(message) from None
    except ytt.TranscriptsDisabled:
        raise RuntimeError(
            "No accessible captions are available for this YouTube video"
        ) from None
    except (ytt.RequestBlocked, ytt.IpBlocked):
        raise RuntimeError(
            "YouTube blocked transcript access from this network"
        ) from None
    except (ytt.YouTubeTranscriptApiException, requests.RequestException):
        raise RuntimeError("YouTube transcript is unavailable") from None

    if not transcript:
        raise RuntimeError(
            "No accessible captions are available for this YouTube video"
        )

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    lines = []
    for snippet in transcript:
        seconds = max(0, int(snippet.start))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        stamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        lines.append(f"[{stamp}] {' '.join(snippet.text.split())}")
    content = "\n".join(lines)
    if output_format.lower() == "json":
        return {
            "url": canonical_url,
            "video_id": video_id,
            "language": transcript.language,
            "language_code": transcript.language_code,
            "is_generated": transcript.is_generated,
            "content": content,
        }
    caption_type = "automatic" if transcript.is_generated else "manual"
    return (
        f"YouTube transcript: {canonical_url}\n"
        f"Language: {transcript.language} ({transcript.language_code}); "
        f"captions: {caption_type}\n\n{content}"
    )

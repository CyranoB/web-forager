#!/usr/bin/env python3
"""
Web Fetch — URL content retrieval with automatic fallback.

Tries a direct HTTP fetch with trafilatura for content extraction first.
Falls back to the Jina Reader API when direct fetch fails, content extraction
fails, or extraction returns insufficient content (e.g., JavaScript-rendered pages,
bot-blocked sites).
"""

import json
import logging
import socket
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Annotated, Any
from urllib.parse import quote, urljoin, urlparse

import requests
import trafilatura
from pydantic import Field

from .server import mcp
from .youtube_transcript import fetch_transcript, video_id_from_url

logger = logging.getLogger(__name__)

# Jina Reader API base URL (used as fallback)
JINA_READER_BASE_URL = "https://r.jina.ai/"

# Minimum content length to consider a direct fetch successful.
# Shorter results likely mean the page blocked us or requires JavaScript.
MIN_CONTENT_LENGTH = 100

# User-Agent for direct fetches — identifies as a bot so sites can
# choose to serve simplified content rather than block outright.
DIRECT_USER_AGENT = (
    "Mozilla/5.0 (compatible; WebForager/3.0; "
    "+https://github.com/CyranoB/web-forager)"
)

# Direct fetch timeout — keep it short so we fall back to Jina quickly
# when a site is slow or unresponsive.
DIRECT_FETCH_TIMEOUT = 15

# Jina fetch timeout — Jina can be slower since it renders JavaScript
JINA_FETCH_TIMEOUT = 30
MAX_REDIRECTS = 10


@dataclass
class _DirectResult:
    content: str | dict[str, Any] | None
    visited_urls: list[str]


def _can_forward(url: str) -> bool:
    """Conservatively identify URLs eligible for third-party forwarding.

    A public address is necessary, not proof that a path is non-sensitive.
    Callers must use allow_jina=False for known confidential resources.
    """
    try:
        _validate_url(url)
        parsed = urlparse(url)
        host = (parsed.hostname or "").rstrip(".").lower()
        if parsed.username is not None or parsed.password is not None:
            return False
        if "?" in url or "#" in url or "%" in host:
            return False
        if "." not in host and ":" not in host:
            return False
        if host.endswith(
            (".local", ".localhost", ".internal", ".lan", ".home", ".onion")
        ):
            return False
        addresses = socket.getaddrinfo(
            host,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
        resolved = [ip_address(address[4][0]) for address in addresses]
        return bool(resolved) and all(
            address.is_global and not address.is_multicast and not address.is_reserved
            for address in resolved
        )
    except (ValueError, OSError):
        return False


def _validate_url(url: str) -> None:
    """Validate that the URL is properly formatted and uses HTTP/HTTPS."""
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    try:
        parsed_url = urlparse(url)
        if not parsed_url.hostname or any(char.isspace() for char in url):
            raise ValueError
        if parsed_url.scheme not in ("http", "https"):
            raise ValueError
        _ = parsed_url.port
    except ValueError:
        raise ValueError("A valid HTTP/HTTPS URL is required") from None


@dataclass(frozen=True)
class _Page:
    content: str
    offset: int
    total_length: int
    next_offset: int | None


def _validate_paging(max_length: Any, offset: Any) -> tuple[int | None, int]:
    """Coerce pagination arguments, rejecting booleans and non-positive lengths."""
    if max_length is not None:
        try:
            if isinstance(max_length, bool):
                raise TypeError
            max_length = int(max_length)
            if max_length <= 0:
                raise ValueError
        except (ValueError, TypeError) as e:
            raise ValueError("max_length must be a positive integer") from e
    if offset is None:
        offset = 0
    try:
        if isinstance(offset, bool):
            raise TypeError
        offset = int(offset)
        if offset < 0:
            raise ValueError
    except (ValueError, TypeError) as e:
        raise ValueError("offset must be a non-negative integer") from e
    return max_length, offset


def _paginate(content: str, max_length: int | None, offset: int) -> _Page:
    """Return one character window of the extracted content."""
    total = len(content)
    if offset and offset >= total:
        raise ValueError(
            f"offset {offset} is beyond the content length ({total} characters)"
        )
    end = total if max_length is None else min(offset + max_length, total)
    return _Page(content[offset:end], offset, total, end if end < total else None)


def _json_text(result: dict[str, Any]) -> tuple[dict[str, Any], str] | None:
    """Locate the text in a JSON result: top-level for direct, under data for Jina."""
    if isinstance(result.get("content"), str):
        return result, result["content"]
    data = result.get("data")
    if isinstance(data, dict) and isinstance(data.get("content"), str):
        return data, data["content"]
    return None


def _apply_page(
    result: str | dict[str, Any], max_length: int | None, offset: int, source: str
) -> str | dict[str, Any]:
    """Slice fetched content and describe how to continue reading it.

    Offsets index the text from one extractor, so results name their source.
    """
    if max_length is None and not offset:
        return result
    if isinstance(result, dict):
        located = _json_text(result)
        if located is None:
            raise ValueError("The fetched JSON has no text content to page")
        holder, text = located
        page = _paginate(text, max_length, offset)
        paged = {**result}
        if holder is result:
            paged["content"] = page.content
        else:
            paged["data"] = {**holder, "content": page.content}
        return paged | {
            "source": source,
            "offset": page.offset,
            "total_length": page.total_length,
            "next_offset": page.next_offset,
        }
    page = _paginate(result, max_length, offset)
    end = page.next_offset or page.total_length
    span = f"characters {page.offset}-{end} of {page.total_length} ({source})"
    if page.next_offset is None:
        return f"{page.content}\n\n[End of content: {span}.]"
    return (
        f"{page.content}\n\n[Truncated: {span}. "
        f"Continue with offset={page.next_offset}.]"
    )


def _direct_fetch(
    url: str,
    output_format: str = "markdown",
    with_images: bool = False,
) -> _DirectResult:
    """
    Fetch a URL directly via HTTP and extract content with trafilatura.

    Preserve every observed destination, including redirects before a failure,
    so the caller can decide whether forwarding is allowed.
    """
    visited = [url]
    html = ""
    try:
        for _ in range(MAX_REDIRECTS + 1):
            _validate_url(visited[-1])
            response = requests.get(
                visited[-1],
                headers={"User-Agent": DIRECT_USER_AGENT},
                timeout=DIRECT_FETCH_TIMEOUT,
                allow_redirects=False,
            )
            try:
                if response.is_redirect or response.is_permanent_redirect:
                    visited.append(urljoin(visited[-1], response.headers["Location"]))
                    continue
                response.raise_for_status()
                html = response.text
                break
            finally:
                response.close()
        else:
            # No forwarding when the destination chain cannot be established.
            return _DirectResult(None, [])
    except (requests.exceptions.RequestException, ValueError, KeyError):
        logger.debug("Direct fetch failed")
        return _DirectResult(None, visited)

    try:
        # Use trafilatura to extract the main content
        content = trafilatura.extract(
            html,
            output_format="markdown",
            include_links=True,
            include_tables=True,
            include_formatting=True,
            include_images=with_images,
        )
    except Exception:
        # Extractor errors can embed page or URL text; keep the observed chain.
        logger.debug("Direct content extraction failed")
        return _DirectResult(None, visited)

    if content is None or len(content) < MIN_CONTENT_LENGTH:
        logger.debug("Direct fetch returned insufficient content")
        return _DirectResult(None, visited)

    logger.debug("Direct fetch successful (%s chars)", len(content))

    if output_format.lower() == "json":
        # Extract metadata for JSON format; the content is usable without it.
        try:
            metadata = trafilatura.bare_extraction(html, with_metadata=True)
            title = getattr(metadata, "title", "") or "" if metadata else ""
        except Exception:
            logger.debug("Direct metadata extraction failed")
            title = ""
        return _DirectResult(
            {
                "url": url,
                "title": title,
                "content": content,
            },
            visited,
        )

    return _DirectResult(content, visited)


def _jina_fetch(
    url: str,
    output_format: str = "markdown",
    with_images: bool = False,
) -> str | dict[str, Any]:
    """Fetch a URL using the Jina Reader API."""
    headers = {"x-no-cache": "true"}

    if output_format.lower() == "json":
        headers["Accept"] = "application/json"

    if with_images:
        headers["X-With-Generated-Alt"] = "true"

    jina_url = f"{JINA_READER_BASE_URL}{quote(url)}"

    logger.debug("Fetching via Jina Reader")
    response = requests.get(
        jina_url, headers=headers, timeout=JINA_FETCH_TIMEOUT, allow_redirects=False
    )
    if response.is_redirect or response.is_permanent_redirect:
        response.close()
        raise RuntimeError("Jina Reader redirected unexpectedly")
    try:
        response.raise_for_status()
        if output_format.lower() == "json":
            content: dict[str, Any] = response.json()
            return content
        return response.text
    finally:
        response.close()


def fetch_url(
    url: str,
    output_format: str = "markdown",
    max_length: int | None = None,
    with_images: bool = False,
    allow_jina: bool = True,
    offset: int = 0,
    language: str | None = None,
) -> str | dict[str, Any]:
    """
    Fetch a URL and convert its content to markdown or JSON.

    YouTube video URLs return timestamped captions. Other URLs use direct HTTP
    extraction, then Jina Reader for eligible URLs when extraction fails.

    Args:
        url: The URL to fetch and convert
        output_format: Output format - "markdown" (default) or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include images in the output
        allow_jina: Allow fallback for eligible public URLs (False for direct-only)
        offset: Character position in the extracted content to start from
        language: Preferred caption language for YouTube videos (for example, "fr")

    Returns:
        The fetched content as markdown string or JSON dict. A paged markdown
        result ends with a marker naming the source and next offset; paged JSON
        adds source and pagination fields.

    Raises:
        ValueError: If the URL, max_length, or offset is invalid
        RuntimeError: If both direct fetch and Jina Reader fail
    """
    _validate_url(url)
    max_length, offset = _validate_paging(max_length, offset)

    video_id = video_id_from_url(url)
    if video_id is not None:
        transcript = fetch_transcript(video_id, output_format, language)
        return _apply_page(transcript, max_length, offset, "youtube")

    # Try direct fetch first
    try:
        result = _direct_fetch(url, output_format, with_images)
    except Exception:
        raise RuntimeError("Direct content extraction failed") from None
    if result.content is not None:
        return _apply_page(result.content, max_length, offset, "direct")

    if (
        not allow_jina
        or not result.visited_urls
        or not all(_can_forward(destination) for destination in result.visited_urls)
    ):
        raise RuntimeError(
            "Direct fetch failed; third-party forwarding is disabled or the URL "
            "is ineligible. Supply the content or use an authorized direct-fetch tool."
        )

    # Fall back to Jina Reader
    try:
        content = _jina_fetch(url, output_format, with_images)
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        raise RuntimeError(
            "Jina Reader failed; source content is unavailable"
        ) from None
    return _apply_page(content, max_length, offset, "jina")


@mcp.tool()
def web_fetch(
    url: str,
    format: str = "markdown",  # noqa: A002 — public MCP tool parameter; renaming would break clients
    max_length: int | None = None,
    with_images: bool = False,
    allow_jina: bool = True,
    # Strict so the MCP schema rejects booleans instead of coercing True to 1.
    offset: Annotated[int, Field(strict=True, ge=0)] | None = 0,
    language: str | None = None,
) -> str | dict[str, Any]:
    """
    Fetch a URL and convert it to markdown or JSON.

    YouTube video URLs return timestamped captions. Other URLs try direct
    HTTP extraction first, then Jina Reader for eligible pages.

    Args:
        url: The URL to fetch and convert
        format: Output format - "markdown" or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include images in page output (not video frames)
        allow_jina: Allow fallback for eligible public URLs (False for direct-only)
        offset: Character position to start from; use the next offset reported
            by a truncated result to continue reading. Offsets are comparable only
            between results from the same source (direct, jina, or youtube)
        language: Preferred caption language for YouTube videos (for example, "fr")

    Returns:
        The fetched content in the specified format (markdown string or JSON object)
    """
    if not url:
        raise ValueError("Missing required parameter: url")

    if format and format.lower() not in ["markdown", "json"]:
        raise ValueError("Format must be either 'markdown' or 'json'")

    max_length, offset = _validate_paging(max_length, offset)

    return fetch_url(
        url,
        output_format=format,
        max_length=max_length,
        with_images=with_images,
        allow_jina=allow_jina,
        offset=offset,
        language=language,
    )


# Backward compatibility alias
jina_fetch = web_fetch

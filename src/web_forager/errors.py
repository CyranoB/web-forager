"""Public failures that must not be confused with successful empty results."""

from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
from requests import HTTPError


class SearchError(RuntimeError):
    """The search provider could not complete the requested search."""


def _confirmed_failure_message(error: Exception) -> str | None:
    """Describe one failure only when its type or HTTP status confirms the cause."""
    status = (
        error.response.status_code
        if isinstance(error, HTTPError) and error.response is not None
        else None
    )
    if isinstance(error, TimeoutException) or status in (408, 504):
        return "timed out. Try again or use another search tool."
    if isinstance(error, RatelimitException) or status == 429:
        return "rate limited. Wait before trying again or use another search tool."
    if status in (502, 503):
        return "backend unavailable. Try again later or use another search tool."
    return None


def provider_search_error(error: Exception, *, news: bool = False) -> SearchError:
    """Translate confirmed provider evidence into a safe public diagnostic."""
    prefix = "News search" if news else "Search"
    pending = [error]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        message = _confirmed_failure_message(current)
        if message is not None:
            return SearchError(f"{prefix} {message}")
        # ddgs can retain an engine's exception as an argument instead of a cause.
        # Inspect exception objects only; their text can include private inputs.
        if isinstance(current, DDGSException):
            pending.extend(arg for arg in current.args if isinstance(arg, Exception))
        if isinstance(current.__cause__, Exception):
            pending.append(current.__cause__)
    return SearchError(
        f"{prefix} failed. Try another search tool; coverage is incomplete."
    )

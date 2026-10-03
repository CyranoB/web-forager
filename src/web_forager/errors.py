"""Public failures that must not be confused with successful empty results."""

from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
from requests import HTTPError


class SearchError(RuntimeError):
    """The search provider could not complete the requested search."""


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
        status = (
            current.response.status_code
            if isinstance(current, HTTPError) and current.response is not None
            else None
        )
        if isinstance(current, TimeoutException) or status in (408, 504):
            return SearchError(
                f"{prefix} timed out. Try again or use another search tool."
            )
        if isinstance(current, RatelimitException) or status == 429:
            return SearchError(
                f"{prefix} rate limited. Wait before trying again or use another search tool."
            )
        if status in (502, 503):
            return SearchError(
                f"{prefix} backend unavailable. Try again later or use another search tool."
            )
        # ddgs can retain an engine's exception as an argument instead of a cause.
        # Inspect exception objects only; their text can include private inputs.
        if isinstance(current, DDGSException):
            pending.extend(arg for arg in current.args if isinstance(arg, Exception))
        if isinstance(current.__cause__, Exception):
            pending.append(current.__cause__)
    return SearchError(
        f"{prefix} failed. Try another search tool; coverage is incomplete."
    )

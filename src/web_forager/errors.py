"""Public failures that must not be confused with successful empty results."""


class SearchError(RuntimeError):
    """The search provider could not complete the requested search."""

#!/usr/bin/env python3
"""
Command line interface for Web Forager.
This module provides the entry point for the `web-forager` command.
"""

import argparse
import json
import logging
import re
import sys
from collections.abc import Callable

from .duckduckgo_news import duckduckgo_news_search
from .duckduckgo_search import duckduckgo_search
from .errors import SearchError
from .server import mcp
from .web_fetch import fetch_url

logger = logging.getLogger(__name__)

# Only Web Forager's own loggers go below WARNING. Dependency loggers record
# request URLs, provider queries, HTTP/2 headers, and MCP payloads at DEBUG or
# INFO, so they inherit the WARNING root level even when debug logging is on.
_APP_LOGGER = "web_forager"
# These providers and transports also log raw failures at WARNING or higher.
_PROVIDER_LOGGERS = ("ddgs", "primp", "httpx", "httpcore")
# FastMCP's argument-validation warnings include the submitted arguments; the
# client already receives that error, so only FastMCP errors are logged.
_FASTMCP_LOGGER = "fastmcp"
# Redact URLs with a scheme and request targets such as "GET /path?sig=...".
_URL = re.compile(
    r"\b[a-z][a-z0-9+.-]*://[^\s'\"<>]+|(?<![\w.])/[^\s'\"<>]*\?[^\s'\"<>]*",
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    return _URL.sub("<redacted URL>", text)


class _RedactURLs(logging.Filter):
    """Replace URLs in emitted records; they can carry tokens or credentials."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(record.getMessage())
        record.args = None
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = logging.Formatter().formatException(record.exc_info)
            # Handlers that render exc_info directly would bypass the redaction.
            record.exc_info = None
        if record.exc_text:
            record.exc_text = _redact(record.exc_text)
        if record.stack_info:
            record.stack_info = _redact(record.stack_info)
        return True


_REDACT_URLS = _RedactURLs()


def _configure_logging(debug: bool) -> None:
    """Log application diagnostics without dependency request payloads."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    logging.getLogger(_APP_LOGGER).setLevel(logging.DEBUG if debug else logging.INFO)
    for logger_name in _PROVIDER_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)
    # FastMCP installs its own non-propagating handlers, which would bypass the
    # redaction filter; route its records through the root handlers instead.
    fastmcp_logger = logging.getLogger(_FASTMCP_LOGGER)
    for handler in fastmcp_logger.handlers[:]:
        fastmcp_logger.removeHandler(handler)
    fastmcp_logger.propagate = True
    fastmcp_logger.setLevel(logging.ERROR)
    for handler in root.handlers:
        handler.addFilter(_REDACT_URLS)


def _handle_version(args: argparse.Namespace) -> int:
    """Handle the version command."""
    from . import __version__

    print(f"Web Forager v{__version__}")

    if getattr(args, "debug", False):
        import platform

        print(f"Python version: {platform.python_version()}")
        print(f"Platform: {platform.platform()}")

        try:
            from ddgs import __version__ as ddgs_version

            print(f"ddgs version: {ddgs_version}")
        except ImportError:
            print("ddgs: not available")

    return 0


def _handle_search(args: argparse.Namespace) -> int:
    """Handle the search command."""
    try:
        query = " ".join(args.query)
        output_format = getattr(args, "output_format", "json")
        results = duckduckgo_search(
            query=query,
            max_results=args.max_results,
            safesearch=args.safesearch,
            output_format=output_format,
        )

        if output_format == "text":
            print(results)
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    except SearchError as error:
        logger.exception("%s", error, exc_info=False)
        return 1
    except Exception:
        logger.error("Search failed. Try another search tool.")
        return 1


def _handle_news(args: argparse.Namespace) -> int:
    """Handle the news command."""
    try:
        query = " ".join(args.query)
        output_format = getattr(args, "output_format", "json")
        results = duckduckgo_news_search(
            query=query,
            max_results=args.max_results,
            safesearch=args.safesearch,
            output_format=output_format,
        )

        if output_format == "text":
            print(results)
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    except SearchError as error:
        logger.exception("%s", error, exc_info=False)
        return 1
    except Exception:
        logger.error("News search failed. Try another search tool.")
        return 1


def _handle_fetch(args: argparse.Namespace) -> int:
    """Handle the fetch command."""
    try:
        result = fetch_url(
            url=args.url,
            output_format=args.format,
            max_length=args.max_length,
            with_images=args.with_images,
            allow_jina=not getattr(args, "direct_only", False),
            offset=args.offset,
            language=args.language,
        )

        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)
        return 0
    except Exception as error:
        # Chained request exceptions can contain signed URLs; omit the traceback.
        logger.exception("Fetch failed: %s", error, exc_info=False)
        return 1


def _handle_serve(args: argparse.Namespace) -> int:
    """Handle the serve command."""
    from . import __version__

    logger.info(f"Starting Web Forager MCP Server v{__version__} (STDIO transport)")
    logger.info("Press Ctrl+C to stop the server")

    # Register "search" as an alias for "duckduckgo_search" for backward compatibility.
    # Some MCP clients may expect the shorter name. This simply delegates to the main tool.
    @mcp.tool()
    def search(
        query: str,
        max_results: int = 5,
        safesearch: str = "moderate",
        output_format: str = "json",
    ) -> list[dict[str, str]] | str:
        """Search DuckDuckGo for the given query."""
        logger.debug(
            "Searching (max_results: %s, safesearch: %s, output_format: %s)",
            max_results,
            safesearch,
            output_format,
        )
        results = duckduckgo_search(query, max_results, safesearch, output_format)
        if isinstance(results, list):
            logger.debug(f"Found {len(results)} results")
        return results

    try:
        mcp.run(transport="stdio")
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception:
        logger.exception("Error running MCP server")
        return 1


def _setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        description="Web Forager - Search and content retrieval via MCP protocol"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve", help="Start the MCP server over STDIO"
    )
    serve_parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search DuckDuckGo directly")
    search_parser.add_argument("query", nargs="+", help="Search query")
    search_parser.add_argument(
        "--max-results", type=int, default=5, help="Maximum number of results to return"
    )
    search_parser.add_argument(
        "--safesearch",
        choices=["on", "moderate", "off"],
        default="moderate",
        help="Safe search setting (default: moderate)",
    )
    search_parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="json",
        dest="output_format",
        help="Output format: 'json' for structured data, 'text' for LLM-friendly (default: json)",
    )

    # News command
    news_parser = subparsers.add_parser("news", help="Search DuckDuckGo news directly")
    news_parser.add_argument("query", nargs="+", help="News search query")
    news_parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of results to return",
    )
    news_parser.add_argument(
        "--safesearch",
        choices=["on", "moderate", "off"],
        default="moderate",
        help="Safe search setting (default: moderate)",
    )
    news_parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="json",
        dest="output_format",
        help="Output format: 'json' for structured data, 'text' for LLM-friendly (default: json)",
    )

    # Fetch command
    fetch_parser = subparsers.add_parser(
        "fetch", help="Fetch and convert content from a URL"
    )
    fetch_parser.add_argument("url", help="URL to fetch content from")
    fetch_parser.add_argument(
        "--direct-only",
        action="store_true",
        help="Fetch directly without Jina forwarding",
    )
    fetch_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    fetch_parser.add_argument(
        "--max-length", type=int, help="Maximum length of content to return"
    )
    fetch_parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Character position to start from, e.g. the next offset of a "
        "truncated result (default: 0)",
    )
    fetch_parser.add_argument(
        "--with-images", action="store_true", help="Generate alt text for images"
    )
    fetch_parser.add_argument(
        "--language", help="Preferred caption language for YouTube videos (e.g. fr)"
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument(
        "--debug", action="store_true", help="Show detailed version information"
    )

    return parser


def main() -> int:
    """Main entry point for the command line interface."""
    parser = _setup_parser()
    args = parser.parse_args()

    _configure_logging(getattr(args, "debug", False))

    # Command dispatch
    handlers: dict[str, Callable[[argparse.Namespace], int]] = {
        "version": _handle_version,
        "search": _handle_search,
        "news": _handle_news,
        "fetch": _handle_fetch,
        "serve": _handle_serve,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

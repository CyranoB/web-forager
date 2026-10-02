"""Read-only synthetic research tools; never fetches from the network."""

import argparse
import json
from pathlib import Path

from fastmcp import FastMCP

from web_forager.web_fetch import _apply_page


def build_server(case: dict, skill_root: Path, trace: Path) -> FastMCP:
    server = FastMCP("skill-fixtures")
    pages = {page["url"]: page for page in case["sources"]}

    def record(tool: str, arguments: dict, result: object) -> object:
        with trace.open("a") as stream:
            stream.write(
                json.dumps({"tool": tool, "arguments": arguments, "result": result})
                + "\n"
            )
        return result

    def search(query: str, max_results: int, tool: str) -> list[dict]:
        if tool in case.get("failed_tools", []):
            record(tool, {"query": query}, {"error": "Provider unavailable"})
            raise RuntimeError("Provider unavailable; search coverage is incomplete")
        selected = case.get("default_results", list(pages))
        for route in case.get("search_routes", []):
            if any(term.casefold() in query.casefold() for term in route["terms"]):
                selected = route["urls"]
                break
        results = [
            {
                "title": pages[url]["title"],
                "url": url,
                "snippet": pages[url].get("snippet", "Open the source for evidence."),
                "date": pages[url].get("date", ""),
            }
            for url in selected[:max_results]
        ]
        record(tool, {"query": query, "max_results": max_results}, results)
        return results

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        }
    )
    def duckduckgo_search(query: str, max_results: int = 8) -> list[dict]:
        """Search the fixture collection from different query angles."""
        return search(query, max_results, "duckduckgo_search")

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        }
    )
    def duckduckgo_news_search(query: str, max_results: int = 10) -> list[dict]:
        """Search news fixtures. Errors are not empty results."""
        return search(query, max_results, "duckduckgo_news_search")

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        }
    )
    def web_fetch(
        url: str,
        allow_jina: bool = True,
        max_length: int | None = None,
        offset: int = 0,
    ) -> str:
        """Read one source. Set allow_jina=False for direct-only access.

        max_length and offset page through long content; a partial result ends
        with the next offset to continue from.
        """
        arguments = {
            "url": url,
            "allow_jina": allow_jina,
            "max_length": max_length,
            "offset": offset,
        }
        if url not in pages or pages[url].get("unavailable"):
            record("web_fetch", arguments, {"error": "Source unavailable"})
            raise RuntimeError("Source unavailable; no source content was read")
        try:
            # Same pagination as the published tool, so the skill sees real markers.
            content = _apply_page(pages[url]["content"], max_length, offset)
        except ValueError as error:
            record("web_fetch", arguments, {"error": str(error)})
            raise
        record("web_fetch", arguments, content)
        return str(content)

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        }
    )
    def read_skill_resource(path: str) -> str:
        """Read a relative Markdown reference belonging to the supplied skill."""
        target = (skill_root / path).resolve()
        if (
            not target.is_relative_to(skill_root.resolve())
            or target.suffix != ".md"
            or not target.is_file()
        ):
            record("read_skill_resource", {"path": path}, {"error": "Unknown resource"})
            raise ValueError("Unknown skill resource")
        content = target.read_text()
        record("read_skill_resource", {"path": path}, content)
        return content

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--skill-root", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    args = parser.parse_args()
    build_server(json.loads(args.case.read_text()), args.skill_root, args.trace).run()

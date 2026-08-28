# Search and fetch fallbacks

Use these routes only when suitable session search or fetch tools are unavailable.

## Packaged CLI

Run Web Forager in an isolated environment:

```bash
uvx --python '>=3.10,<3.14' web-forager search "your query" --max-results 8 --output-format json
uvx --python '>=3.10,<3.14' web-forager fetch "https://example.com" --format markdown
```

## Search fallback

If packaged search fails, run `ddgs` without changing the current project environment:

```bash
uv run --no-project --python '>=3.10,<3.14' --with 'ddgs>=9.5.2' python - <<'PY'
from ddgs import DDGS
results = DDGS().text(query="your query", max_results=8)
for r in results:
    print(r["title"], r["href"], r["body"])
PY
```

## Fetch fallback

If packaged fetch fails, use Jina Reader only for a public URL with no credentials,
signed parameters, private hostname, or sensitive identifier. This sends the complete
URL to a third party:

```bash
curl -s "https://r.jina.ai/https://example.com"
```

The workflow requires both search and fetch. Report a missing capability or failed
source instead of filling the gap from snippets or assumptions.

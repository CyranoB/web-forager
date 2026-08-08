---
name: competitive-intel
license: MIT
metadata:
  author: CyranoB
  version: "2.1.0"
description: >
  Map a competitive market or position the user's product against competitors.
  Use for builders and sellers evaluating market players, gaps, differentiation,
  pricing, or strategic threats.
---

# Competitive Intel

Produce strategic intelligence for someone building or selling a product.

## Choose one mode

- **Market landscape:** the user wants to discover and categorize players, market
  dynamics, or white space. Read [market-landscape.md](market-landscape.md) completely,
  then follow it.
- **Competitive positioning:** the user wants to compare their product with named or
  discoverable competitors. Read
  [competitive-positioning.md](competitive-positioning.md) completely, then follow it.

Use market landscape for “what exists?” and competitive positioning for “where do we
stand?” If the user's intent does not settle the mode, ask one focused question.

## Tools and evidence

Use available web search and URL-fetch tools. Prefer callable names ending in
`duckduckgo_search` and `web_fetch`; client-added prefixes vary, so inspect the tools in
the session. Without session tools, run the packaged CLI in an isolated environment:

```bash
uvx --python '>=3.10,<3.14' web-forager search "your query" --max-results 8 --output-format json
uvx --python '>=3.10,<3.14' web-forager fetch "https://example.com" --format markdown
```

If `uvx` cannot run the packaged search, use `ddgs` without touching the current
project environment:

```bash
uv run --no-project --python '>=3.10,<3.14' --with 'ddgs>=9.5.2' python - <<'PY'
from ddgs import DDGS
results = DDGS().text(query="your query", max_results=8)
for r in results:
    print(r["title"], r["href"], r["body"])
PY
```

If packaged fetch fails, use Jina Reader:

```bash
curl -s "https://r.jina.ai/https://example.com"
```

The workflow requires both search and fetch. If either capability is unavailable, state
what is missing instead of producing unsupported intelligence.

Markets move quickly. Use `[current year]` in discovery queries and prefer current
official product, pricing, and changelog pages. Use older sources only for history, and
label estimates and inference.

## Shared quality bar

- Read every source used for a material comparison or recommendation.
- Prefer first-party pages for capabilities, prices, and product direction.
- Use independent reviews and community discussions for perception and pain points.
- Separate the user's claims about their product from independently verified facts.
- Cite material claims near the text they support.

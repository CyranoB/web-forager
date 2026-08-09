---
name: tech-advisor
license: MIT
metadata:
  author: CyranoB
  version: "2.2.0"
description: >
  Advise a technology choice through current evidence. Use for choosing tech
  products for a concrete use case, or assessing whether a technology is mature
  enough to adopt.
---

# Tech Advisor

Make a current, evidence-backed technology recommendation for a specific user or team.

## Choose one mode

- **Maturity assessment:** one technology is being considered for adoption. Read
  [maturity-assessment.md](maturity-assessment.md) completely, then follow it.
- **Product comparison:** two or more products, or a product category, must be chosen
  for a concrete use case. Read [product-comparison.md](product-comparison.md)
  completely, then follow it.

Use maturity assessment for “is this ready?” and product comparison for “which should I
choose?” If intent does not settle the mode, ask one focused question.

## Tools and evidence

Use available web search and URL-fetch tools. Prefer callable names ending in
`duckduckgo_search` and `web_fetch`; client-added prefixes vary, so inspect the tools in
the session. Without session tools, run the packaged CLI in an isolated environment:

```bash
uvx --python '>=3.10,<3.14' web-forager search "your query" --max-results 8 --output-format json
uvx --python '>=3.10,<3.14' web-forager fetch "https://example.com" --format markdown
```

If `uvx` cannot run packaged search, use `ddgs` without touching the current project
environment:

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
what is missing instead of recommending from stale knowledge.

Technology changes quickly. Use `[current year]` in queries, verify the exact current
model or version, and prefer recent first-party specifications plus current independent
evidence. Label estimates and inference.

## Shared quality bar

- Read every source used for a material comparison or recommendation.
- Match evidence to the user's region, constraints, and use case.
- Include total cost and meaningful tradeoffs, not only headline specifications.
- Cite material claims near the text they support.
- Take a position when the evidence supports one; state what would change it.

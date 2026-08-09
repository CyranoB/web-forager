---
name: deep-research
license: MIT
metadata:
  author: CyranoB
  version: "1.2.0"
description: >
  Research broad, current questions through multi-angle web search, selective
  full-page reading, and cited synthesis. Use for a general investigation or deep
  dive whose answer spans multiple sources or perspectives.
---

# Deep Research

Answer broad, current questions with multi-angle search, source reading, and cited
synthesis.

## Tools

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

The workflow requires both search and fetch. If either capability is unavailable,
state what is missing instead of inventing results.

## Workflow

### 1. Frame the question

Identify the core question, the decisions the answer should support, and the distinct
angles needed for coverage. Ask only when an unresolved ambiguity would materially
change the research.

**Complete when:** the question and every necessary research angle are explicit.

### 2. Search multiple angles

Run 2–3 searches with meaningfully different framings: direct, specific, and an
alternative perspective. For fast-moving topics, use `[current year]` in queries.
Evaluate all snippets before choosing pages.

**Complete when:** every angle has search results and the candidate set contains
relevant, diverse, and sufficiently current sources.

### 3. Read the evidence

Read the 3–5 strongest pages. Prefer primary and authoritative sources, then reputable
secondary analysis. Diversify domains. If a page fails, replace it or record the gap.

**Complete when:** every material finding is supported by a source that was read in
full, and important disagreements or missing evidence are identified.

### 4. Synthesize

Scale the answer to the question:

- **Quick answer:** 2–4 direct sentences with inline source links.
- **Standard report:** summary, key findings, and annotated sources.
- **Deep dive:** summary, key findings, 2–4 topic sections, limitations, and annotated
  sources.

Use a quick answer for a narrow factual question. A standard report is the default. Use
a deep dive when the user requests depth or the question has multiple independently
necessary angles that cannot be synthesized clearly in the standard report. Research
depth stays high across all three formats; expose only the findings and sources needed
to answer the question.

Cite specific claims near the text they support. Prefer concrete dates, numbers, names,
and versions. Separate sourced facts from inference.

**Complete when:** the core question is answered directly, every material factual claim
is cited, uncertainty is visible, and repetitive or irrelevant material has been cut.

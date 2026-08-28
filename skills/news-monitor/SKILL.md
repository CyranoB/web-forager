---
name: news-monitor
license: MIT
metadata:
  author: CyranoB
  version: "1.3.0"
description: >
  Monitor recent developments on a topic and produce a chronological, source-read
  briefing. Use when recency or a stated time window is the core question.
---

# News Monitor

Find distinct recent events, read a source for each event described in detail, and
deliver a chronological briefing.

## Tools

Use an available news-search tool, preferring a callable name ending in
`duckduckgo_news_search`. Use regular search ending in `duckduckgo_search` only to fill
coverage gaps. Read pages with a fetch tool ending in `web_fetch`. Client-added prefixes
vary, so inspect the tools in the session.

Without session tools, run the packaged CLI in an isolated environment:

```bash
uvx --python '>=3.10,<3.14' web-forager news "your query" --max-results 10 --output-format json
uvx --python '>=3.10,<3.14' web-forager fetch "https://example.com" --format markdown
```

If `uvx` cannot run packaged news search, use `ddgs` without touching the current
project environment:

```bash
uv run --no-project --python '>=3.10,<3.14' --with 'ddgs>=9.5.2' python - <<'PY'
from ddgs import DDGS
results = DDGS().news(query="your query", max_results=10)
for r in results:
    print(r["date"], r["title"], r["url"], r["source"])
PY
```

If packaged fetch fails, use Jina Reader:

```bash
curl -s "https://r.jina.ai/https://example.com"
```

The workflow requires both search and fetch; state what is missing if either is
unavailable.

## Workflow

### 1. Set the window

Identify the topic, time frame, and angle. Use the user's window when supplied;
otherwise cover the last 2–4 weeks. Ask only when an unresolved ambiguity would
materially change the search.

**Complete when:** the inclusion window and topic boundaries are explicit.

### 2. Search for events

Run 1–2 news searches with distinct angles and `[current year]` where useful. Combine
the results before selecting stories.

**Complete when:** the result set covers the topic from more than one query angle, or
one query demonstrably exhausts the narrow topic.

### 3. Deduplicate and filter

Group coverage of the same event, discard results outside the window, and select the
best candidate source for each event. Aim for 3–7 distinct events.

**Complete when:** every retained item represents a distinct in-window event with a
publication date and candidate source.

### 4. Read every detailed event

Fetch at least one authoritative source for each event that will receive a detailed
summary. Prefer primary announcements and direct reporting. Search snippets may support
headline discovery only; they are not evidence for explanatory claims. If an event's
source cannot be read, replace it or omit the detailed event and record the coverage gap.

**Complete when:** every detailed event has at least one fetched source supporting what
happened, why it matters, and any stated next step.

### 5. Deliver the briefing

Present most recent first. The default briefing uses a single event list:

- period covered, current update date, and a one-sentence bottom line;
- 3–5 priority events, each with a headline and 1–2 sourced sentences covering what
  happened and why it matters;
- remaining significant events, when present, as one-line additional developments;
- a short “What to watch” section grounded in sourced upcoming events or unresolved
  threads.

Use an expanded briefing with 2–4 sentences per event only when the user asks for
comprehensive coverage or an event needs that detail to avoid a misleading summary.
Each event headline serves as both navigation and detail heading, so the event appears
once.

If no significant developments survive filtering, say so plainly and give the searched
window.

**Complete when:** all events are distinct and in-window, every detailed claim cites a
read source, dates are explicit, and inference is labeled.

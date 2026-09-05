---
name: news-monitor
license: MIT
metadata:
  author: CyranoB
  version: "1.4.0"
description: >
  Monitor recent developments on a topic and produce a chronological, source-read
  briefing. Use when recency or a stated time window is the core question.
---

# News Monitor

Find distinct recent events, read a source for every published event, and
deliver a chronological briefing.

## Tools

Before using tools, read [source-access.md](source-access.md) completely.

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

Start with 1–2 news searches with distinct angles and `[current year]` where useful.
Combine the results before selecting stories. Check their distribution across the
requested period, relevant subtopics, and independent outlets. If results cluster on
one date, outlet, or subtopic, expand with narrower subperiods, focused queries, and
primary announcements. Use regular search to recover coverage gaps, including a failed
news provider. Keep failed searches separate from successful searches with no matches.
Event counts are presentation targets, not evidence that discovery is complete.

**Complete when:** relevant subperiods and subtopics have been searched, additional
queries mostly repeat known events, and any remaining coverage gaps or tool failures
are explicit. One query suffices only when it demonstrably exhausts a narrow topic.

### 3. Deduplicate and filter

Group coverage of the same event and record both the event date and publication date.
Filter by the date of the actual development, then select the best candidate source
for each event. A recent republication or retrospective does not make an old event new.
Include newly reported historical events only when the disclosure itself is a material
in-window development; label it as a new disclosure and distinguish its date from the
underlying event date. Aim for 3–7 distinct events.

**Complete when:** every retained item represents a distinct in-window event with a
development date, separate publication date, and candidate source. Unknown dates are
marked explicitly; items without a supported in-window development remain candidates
until source reading resolves the date, or are omitted with a coverage gap.

### 4. Read every published event

Fetch at least one authoritative source for every event included in the briefing,
including headlines and one-line additional developments. Prefer primary announcements and direct reporting. Search snippets may support
headline discovery only; they are not evidence for explanatory claims. If an event's
source cannot be read, replace it or omit that event and record the coverage gap.

**Complete when:** every published event has at least one fetched source supporting what
happened, its development date, why it matters, and any stated next step. Recheck window
eligibility against the read source before retaining the event.

### 5. Deliver the briefing

Present most recent first by development date, using the disclosure date for newly
reported historical events and showing the underlying date or its uncertainty.
The default briefing uses a single event list:

- period covered, current update date, and a one-sentence bottom line;
- 3–5 priority events, each with a headline and 1–2 sourced sentences covering what
  happened and why it matters;
- remaining significant events, when present, as cited one-line additional developments;
- a short “What to watch” section grounded in sourced upcoming events or unresolved
  threads.

Use an expanded briefing with 2–4 sentences per event only when the user asks for
comprehensive coverage or an event needs that detail to avoid a misleading summary.
Each event headline serves as both navigation and detail heading, so the event appears
once.

If successful discovery and filtering find no significant developments, say so and give
the searched window. If failures or unread sources prevent adequate coverage, report
that coverage is incomplete rather than asserting a quiet period.

**Complete when:** all events are distinct and in-window, every event and explanatory claim cites a
read source, dates are explicit, and inference is labeled.

---
name: fact-check
license: MIT
metadata:
  author: CyranoB
  version: "1.3.0"
description: >
  Fact-check a specific, verifiable claim by seeking supporting and contradicting
  evidence, weighing source quality, and issuing a calibrated verdict with citations.
---

# Fact Check

Test a specific claim against evidence on both sides and issue a calibrated verdict.

## Tools

Before using tools, read [source-access.md](source-access.md) completely.

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
return `UNVERIFIED` and name the missing capability.

## Workflow

### 1. Extract the claims

Turn the user's statement into specific, independently verifiable claims. Separate
compound claims. If wording is subjective, explain that it can be contextualized but
cannot receive a factual verdict. Continue immediately when the claim is clear; ask for
confirmation only when two plausible interpretations would change the evidence sought.

Normalize each factual claim's entity, metric and units, population, geography, and
relevant date where applicable. Preserve the original meaning and make material
assumptions explicit. Establish whether the user wants publication-time evidence,
a current assessment, or both; judge an explicitly historical statement at its stated
date and label later developments separately. Otherwise use the current date as cutoff.

Treat an unexpired forecast as a prediction with a horizon and assumptions. Assess its
support and likelihood; an unlikely prediction is not FALSE merely because its deadline
has not arrived. Check its factual premises separately.

**Complete when:** every factual claim has a testable meaning and temporal frame;
subjective statements and forecasts are distinguished from established facts.

### 2. Seek support

Search for primary evidence that would confirm each claim. Use direct paraphrases,
official statements, and queries for the exact metric or event.

**Complete when:** each claim has the strongest available supporting evidence, or the
absence of support is recorded.

### 3. Seek contradiction

Actively search for counterevidence, corrections, alternative measurements, and credible
disagreement. Do not treat failure to find a debunk as confirmation.

**Complete when:** every claim has received a genuine adversarial search, not merely a
second confirming query.

### 4. Read and weigh sources

Read enough decisive evidence for each atomic claim, starting with the strongest sources
on both sides and expanding when a claim remains unsupported or disputed. A total source
count is not a coverage criterion. Search snippets are discovery aids, not verdict evidence.
Evaluate authority, specificity, recency, independence, and conflicts of interest.
Trace corroborating reports to their underlying records: repeated publication of one
study, release, or wire report is one evidence chain. Read the relevant methods,
definitions, qualifications, and quotation context before drawing a conclusion.

**Complete when:** every atomic claim has read evidence addressing its exact scope and
time frame, or a named gap; independence and material source limitations are explicit.
Stop when further searches repeat evidence without a realistic prospect of changing
the verdict; unresolved gaps remain UNVERIFIED rather than triggering invented support.

### 5. Deliver the verdict

Use this scale:

- **CONFIRMED:** independent authoritative evidence agrees, or a definitive primary
  record directly establishes the exact fact; no credible contradiction survives review.
- **LIKELY TRUE:** strong support remains, with minor gaps or caveats.
- **NEEDS CONTEXT:** the core fact holds, but its scope, certainty, or significance is
  overstated. Explain the missing baseline or qualifier; use FALSE when the core fact fails.
- **UNVERIFIED:** strong evidence is unavailable in either direction.
- **DISPUTED:** credible sources materially disagree.
- **FALSE:** strong evidence contradicts the claim and support is weak or absent.

Default to a compact verdict for one claim:

1. state the claim and verdict first;
2. explain the decisive support and contradiction in 2–4 sentences;
3. add only caveats that could change how the verdict is understood;
4. cite the decisive read sources, annotated by role; use only as many as needed.

For multiple extracted claims, repeat the compact block for each. Use a source-by-source
account only when the user requests it or a material conflict cannot be explained
compactly. State explicitly when one side produced no evidence.

**Complete when:** every extracted factual claim has a verdict, both search directions are
accounted for, decisive evidence is cited, and confidence matches the limitations.

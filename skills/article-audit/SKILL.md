---
name: article-audit
license: MIT
metadata:
  author: CyranoB
  version: "1.1.0"
description: >
  Audit a full article for factual accuracy, missing counter-voices, numerical
  context, and promotional or one-sided framing. Use when a user shares an
  article or URL and asks whether it is accurate, credible, balanced, or PR.
---

# Article Audit

Test whether a whole article gives a fair picture. Extract its load-bearing claims,
verify them independently, seek the voices it omits, and check whether accurate
numbers create an inaccurate impression. For one isolated claim, use `fact-check`.

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

The audit requires the complete article, search, and fetched evidence. If any are
unavailable, report the resulting limit instead of filling the gap from snippets or
assumption.

## Workflow

### 1. Read and scope

Fetch the URL or use the supplied text, then read the complete article before checking
individual statements. Identify its thesis, intended takeaway, cited voices, and their
interests. Extract 4–8 specific, verifiable claims that carry the argument: figures,
quotes, comparisons, causal statements, or forecasts. Skip pure opinion and incidental
details. Split compound statements so each selected claim can receive one verdict.
Before searching, show a numbered audit scope with the selected claims.

**Complete when:** the thesis and intended takeaway are explicit, every selected claim
is atomic and could be disproved by evidence, the scope is visible, and omitting any
remaining claim would not materially change the article's credibility assessment.

### 2. Test the evidence

For each claim, seek both corroboration and contradiction outside the article's source
chain. Prefer primary records and authoritative independent analysis. Treat a subject's
press release, spokesperson, investor, partner, or commissioned research as evidence of
its position, not independent confirmation. Read the decisive pages in full and note
when qualifiers, ranges, dates, or uncertainty differ from the article's wording.
Search snippets are discovery aids, not verdict evidence: fetch and read every source
used to decide a claim. Keep a claim ledger recording support, challenge, source
interests, and gaps.

**Complete when:** every claim has received genuine supporting and adversarial searches,
every verdict source has been read in full, and its ledger records evidence on both
sides—or explicitly records that a deliberate search found none.

### 3. Find counter-voices

Search for credible perspectives the article leaves out: independent researchers,
regulators, standards bodies, critics, competing methods, failure cases, and relevant
historical track records. Compare those voices with the article's quoted sources. An
absence matters only after a deliberate search; distinguish "not quoted" from "not
found."

**Complete when:** every major theme has an independent or dissenting perspective, or a
documented search that found none, and every quoted source's material stake is clear.

### 4. Check scale

Choose the context test that matches each important number or forward-looking claim:

- **Denominator:** share of the relevant whole or market.
- **Base rate:** absolute risk and a meaningful comparison period or group.
- **Representativeness:** sample size, selection, and population implied by the article.
- **Novelty:** prior instances behind "first," "unprecedented," or similar language.
- **Track record:** outcomes of comparable forecasts, roadmaps, or past promises.

Use independent baseline data where available. Explain when a technically accurate
number overstates magnitude, certainty, novelty, or representativeness.

**Complete when:** every material quantitative or predictive claim has the applicable
denominator, baseline, comparison, or precedent—or the missing context is identified.

### 5. Judge claims and framing

Assign each claim exactly one unchanged verdict label:

- **CONFIRMED:** multiple authoritative sources agree; no credible contradiction remains.
- **LIKELY TRUE:** strong support remains after minor gaps or caveats.
- **NEEDS CONTEXT:** the core fact holds, but its scope, certainty, or significance is
  overstated.
- **DISPUTED:** credible evidence materially conflicts.
- **UNVERIFIED:** independent evidence is insufficient.
- **FALSE:** strong evidence contradicts the claim.

Then judge the article separately: balanced, factual but slanted, promotional, or
materially misleading. A set of true claims can still produce misleading framing.

**Complete when:** every selected claim has a calibrated verdict, and the framing
judgment follows from sourcing balance, omissions, and scale rather than tone alone.
Use exactly one label, unchanged; put qualifications in the rationale.

## Report

Write in the user's language and use this structure:

1. **Bottom line:** two or three sentences on factual reliability and framing.
2. **Claims audited:** each atomic claim, unchanged verdict label, concise rationale,
   supporting evidence, and contradicting evidence—or `none found after search`.
3. **Missing voices:** omitted perspectives and disclosed interests of quoted sources.
4. **Scale and context:** denominators, base rates, comparisons, or precedents that
   change how the claims should be read.
5. **Framing assessment:** the overall judgment and its strongest reason.
6. **Sources:** annotate every link as support, challenge, baseline, or context; disclose
   material interests.

Separate sourced findings from inference. State when a search produced no independent
evidence, and keep confidence proportional to the evidence.

**Complete when:** the report accounts for every scoped claim, both search directions,
every missing or interested voice, the applicable scale check, and every source's role.

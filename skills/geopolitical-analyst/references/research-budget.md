# Research budget and execution

## Default focused assessment

For one supplied article or a focused geopolitical question, use these ceilings,
not quotas:

- Verify the three most consequential claims; fewer when sufficient.
- Use at most two discovery batches, each with up to three targeted search queries.
- Read at most five useful corroborating sources beyond the supplied article;
  three to five are usually sufficient, and fewer are preferable when decisive.
- Aim to begin synthesis within three minutes of research. This is a soft target,
  not a guarantee; use available timestamps without adding clock-polling loops.

Failed fetches and replacement sources still consume time and discovery capacity;
they do not reset the budget. Apply the per-source recovery limit in
[source-access.md](../source-access.md).

Once the central argument and consequential claims can be assessed, synthesize.
Stop earlier when new results repeat the same evidence. Do not fill remaining
source or query allowances for their own sake.

Exceed a ceiling only to resolve a specific uncertainty that could materially
change the verdict. Identify the uncertainty and the next evidence needed, make
one targeted follow-up batch, then synthesize with any remaining limitation.
Do not repeatedly extend the budget. If access delays consume the time target,
finish the pending retrieval and assess whether the existing evidence is sufficient
before starting more work. Never invent evidence or omit a material qualification
to meet a budget.

Explicit requests for comprehensive or deep analysis can use a larger scope.
Set a finite claim, source, and discovery budget appropriate to that request before
researching, and retain the same recovery limits and stopping discipline.
User-specified scope and limits take precedence.

## Reduce model round trips

- Use relevant search, fetch, and browser capabilities only. Do not probe unrelated
  connectors, search private work documents, or call status tools with invented IDs.
- Batch independent searches or fetches in one parallel execution when supported.
  Keep dependent retrievals sequential.
- With a CLI, allow ordinary searches and fetches time to finish: prefer an initial
  wait of 10–30 seconds within tool limits instead of one second. If processes remain
  active, collect their results together where supported. Poll only actual running
  jobs; avoid separate size checks, empty polls, or terminal inspection as progress
  substitutes. Keep waits short enough to communicate progress.
- Reuse skill text already loaded in the conversation. Read additional references
  once, when needed, rather than reloading the same bundle.

## Keep evidence compact

Save full fetched pages locally when file tools are available, and inspect the
article body without navigation, footers, unrelated recommendations, or HTML dumps.
Preserve titles, dates, attribution, qualifications, and relevant chart captions.
If boilerplate remains, extract the main body locally before returning it to the
model. If local processing is unavailable, request bounded extracts and retrieve
additional passages only when needed for a material claim.

Read each source once and keep a short evidence ledger: URL, access status, date,
claim supported or challenged, and material gaps. For a subsequent check, retrieve
only the relevant passage. Do not repeatedly return the whole source or the ledger.
An output-length limit is not evidence of completeness: retrieve missing context
when it could change the conclusion, subject to the recovery budget.

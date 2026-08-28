# README writing guide

Use this guide for prose and structural changes to `README.md`. For command-only
updates, preserve the surrounding style and verify the command against the current
CLI or configuration.

## Reader and purpose

- Write for a technically capable reader encountering Web Forager for the first
  time.
- Lead with what the reader can accomplish, then give the shortest runnable path.
- Explain user-visible behavior before implementation detail.
- Keep installation and usage instructions copy-pasteable and self-contained.

## Voice

- Preserve the opening vignette's dry, specific personality. Use the rest of the
  README for direct, practical documentation.
- Use concrete nouns, active verbs, short paragraphs, and sentence-case headings.
- Make confident claims only when the repository or a cited source supports them.
- Prefer plain transitions and varied sentence shapes. Cut generic framing,
  promotional superlatives, canned conclusions, repeated summaries, and forced
  contrasts.
- Use jokes, metaphors, and em dashes sparingly; each should improve the sentence
  rather than decorate it.

## Structure

- Put the common path before alternatives and advanced configuration.
- Use code blocks for commands, tables for repeated comparisons, and disclosure
  blocks for long tool-specific setup.
- Keep each explanation in one canonical section and link back to it instead of
  repeating it.
- Preserve established anchors and headings unless the change intentionally
  reorganizes the document.

## Accuracy

- Verify skill names and counts, supported Python versions, installation commands,
  CLI flags, MCP configuration, and tool behavior against the repository.
- Update every README occurrence of a changed public fact.
- Distinguish the default skill-first workflow from the optional MCP server and CLI.

## Completion

Read the finished diff as a new user. Every command must be runnable in sequence,
every public claim must match its source of truth, and every section must add
information rather than restate an earlier section.

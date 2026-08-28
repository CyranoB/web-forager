# Web Forager

![Illustration of a determined scribe wielding a giant quill fighting a tangle of papers and monsters, with a duck in a cap at his side and stacks of documents and crates behind](assets/header.png)

[![PyPI](https://img.shields.io/pypi/v/web-forager?style=flat-square)](https://pypi.org/project/web-forager/)
[![Python Version](https://img.shields.io/pypi/pyversions/web-forager?style=flat-square)](https://pypi.org/project/web-forager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/web-forager/month)](https://pepy.tech/project/web-forager)
[![skills.sh](https://skills.sh/b/CyranoB/web-forager)](https://skills.sh/CyranoB/web-forager)

*The thing about information on the web is that it doesn't want to be found. It hides behind cookie banners, contradicts itself across twelve tabs, and occasionally insists that a press release counts as independent evidence. Web Forager goes looking anyway, accompanied by a duck of questionable temperament. It searches, reads, checks claims, follows the news, maps competitors, evaluates technology, and attempts to explain why governments are glaring at one another. It reads the links and brings back a cited answer.*

Web Forager gives AI agents practical web research workflows as **Agent Skills**.
The skills search DuckDuckGo, monitor news, fetch pages, and synthesize cited answers.

Default usage is skill-first. You do not need to configure an MCP server to use the
research workflows.

## Quickstart

Install all seven skills with one command. It works for 50+ coding agents:

```bash
npx skills@latest add CyranoB/web-forager
```

The installer detects your agents, asks which skills you want, and places them in
the right location.

Common variations:

```bash
npx skills@latest add CyranoB/web-forager --list
npx skills@latest add CyranoB/web-forager --skill deep-research
npx skills@latest add CyranoB/web-forager --skill '*' -a claude-code -a codex -y
```

## Install for your coding tool

Install as skills/plugins when your agent supports them. Use MCP only when your tool
does not support skills, or when you want raw search/fetch tools instead of guided
research workflows.

<details>
<summary><strong>Claude Code</strong></summary>

Install all seven skills from the plugin marketplace:

```bash
/plugin marketplace add CyranoB/web-forager
/plugin install forager-skills@web-forager
```

Restart Claude Code, then check `/skills`.

The Quickstart command above is also available as a cross-agent install path.

MCP-only fallback:

```bash
claude mcp add --transport stdio web-forager -- uvx --python ">=3.10,<3.14" web-forager serve
```

</details>

<details>
<summary><strong>Codex</strong></summary>

Install the skills for the current project:

```bash
npx skills@latest add CyranoB/web-forager -a codex
```

Install globally instead:

```bash
npx skills@latest add CyranoB/web-forager -a codex -g
```

MCP-only fallback:

```bash
codex mcp add web-forager -- uvx --python ">=3.10,<3.14" web-forager serve
```

</details>

<details>
<summary><strong>VS Code / GitHub Copilot</strong></summary>

If your VS Code build supports agent plugins, use the command palette:

1. Open `Cmd+Shift+P` on macOS or `Ctrl+Shift+P` on Windows/Linux.
2. Run `Chat: Install Plugin From Source`.
3. Paste `https://github.com/CyranoB/web-forager`.

MCP-only fallback: configure a local MCP server with the standard config below.

</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

Install the skills for the current project:

```bash
npx skills@latest add CyranoB/web-forager -a gemini-cli
```

Install globally instead:

```bash
npx skills@latest add CyranoB/web-forager -a gemini-cli -g
```

MCP-only fallback:

```bash
gemini mcp add web-forager uvx --python ">=3.10,<3.14" web-forager serve
```

</details>

<details>
<summary><strong>Pi Coding Agent</strong></summary>

Install the skills for the current project:

```bash
npx skills@latest add CyranoB/web-forager -a pi
```

Install globally instead:

```bash
npx skills@latest add CyranoB/web-forager -a pi -g
```

For one-off sessions from a local checkout, pass a skill path explicitly:

```bash
pi --skill web-forager/skills/deep-research
```

MCP-only fallback: configure a local MCP server with the standard config below.

</details>

<details>
<summary><strong>Kiro CLI</strong></summary>

Install the skills for the current workspace:

```bash
npx skills@latest add CyranoB/web-forager -a kiro-cli
```

Install globally instead:

```bash
npx skills@latest add CyranoB/web-forager -a kiro-cli -g
```

Kiro's default agent loads skills from both locations automatically. For custom
agents, add skill resources such as:

```json
{
  "resources": [
    "skill://.kiro/skills/*/SKILL.md",
    "skill://~/.kiro/skills/*/SKILL.md"
  ]
}
```

</details>

<details>
<summary><strong>Cursor, OpenCode, Cline, Windsurf, JetBrains</strong></summary>

Use the standard MCP config below unless your client supports Agent Skills or plugins
from a GitHub repository. If it does, install from:

```text
https://github.com/CyranoB/web-forager
```

</details>

### Individual skills

For any Agent Skills-compatible tool, install one skill by name:

```bash
npx skills@latest add CyranoB/web-forager --skill deep-research
```

Direct skill URLs also work:

```bash
npx skills@latest add https://github.com/CyranoB/web-forager/tree/main/skills/deep-research
```

## Use the skills

After installing, ask your agent naturally. The matching skill should be selected
automatically by skill metadata.

Examples:

```text
Research the current state of open-source browser agents.
Fact check: did Apple announce a foldable iPhone?
Audit this article for accuracy and framing: https://example.com/article
What's new with Anthropic this month?
Map the competitive landscape for AI meeting assistants.
Should we adopt Bun for a production Node service?
Analyze whether Russia and NATO are already in a hybrid conflict.
```

## Available skills

| Skill | Use it for | Output |
| --- | --- | --- |
| [article-audit](skills/article-audit/) | Auditing a full article's accuracy, omissions, and framing | Per-claim verdicts and framing assessment |
| [deep-research](skills/deep-research/) | General research, lookups, deep dives | Adaptive report with citations |
| [fact-check](skills/fact-check/) | Verifying a specific claim | Verdict with supporting and contradicting evidence |
| [news-monitor](skills/news-monitor/) | Recent news and updates | Chronological briefing |
| [competitive-intel](skills/competitive-intel/) | Market maps and competitor analysis | Landscape or positioning report |
| [tech-advisor](skills/tech-advisor/) | Tech/product evaluation and adoption decisions | Recommendation with evidence |
| [geopolitical-analyst](skills/geopolitical-analyst/) | Geopolitical assessments, conflicts, policies, scenarios, and narrative audits | Sourced assessment with calibrated confidence |

### Article audit

Use [`article-audit`](skills/article-audit/) to check an article's facts, omissions, and
framing. It selects the 4-8 claims on which the argument depends and searches for
independent evidence on both sides. It checks quoted sources for material interests,
looks for credible voices the article leaves out, and tests important numbers or
forecasts against denominators, base rates, comparisons, and past results.

The report gives a bottom line, a verdict for each claim, missing evidence and context,
a framing judgment, and annotated sources. It rates facts and framing separately, so it
can show when accurate claims create a one-sided or misleading picture. Verdicts range
from `CONFIRMED` to `FALSE`. To check one claim, use
[`fact-check`](skills/fact-check/).

### Deep research

Use [`deep-research`](skills/deep-research/) for a broad, current question that needs
several sources or points of view. It frames the question, searches 2-3 different angles,
and reads the 3-5 strongest pages. It favors primary and authoritative sources and
records important disagreements or gaps.

The skill can return a short cited answer, a standard report, or a deep dive with topic
sections and limitations. It cites material facts where they appear and labels its own
inferences.

### Fact check

Use [`fact-check`](skills/fact-check/) to test a specific claim. It splits compound
statements into testable parts and searches for support and counterevidence. It weighs
each source by its authority, specificity, recency, independence, and conflicts of
interest. A missing rebuttal is not proof.

Each claim receives one verdict: `CONFIRMED`, `LIKELY TRUE`, `UNVERIFIED`, `DISPUTED`,
or `FALSE`. The response explains the verdict, presents evidence from both sides, and
lists caveats and sources. To assess a whole article, use
[`article-audit`](skills/article-audit/).

### News monitor

Use [`news-monitor`](skills/news-monitor/) when the answer depends on recent events or a
set time period. Unless the user chooses a period, it covers the previous 2-4 weeks. It
searches from more than one angle, groups reports of the same event, and removes stories
outside the window. It reads at least one authoritative source for every event it
describes in detail.

The briefing puts the newest events first and gives dates, short summaries, and stated
next steps. It also explains why each event matters. Its watch list covers sourced
upcoming events and unresolved threads. Search snippets help find stories; they do not
support the briefing's claims.

### Competitive intelligence

Use [`competitive-intel`](skills/competitive-intel/) in one of two modes. Market
landscape maps the players, prices, barriers, and gaps in a market. Competitive
positioning compares a user's product with its closest rivals, including their
capabilities, prices, customer complaints, recent moves, and threat level.

The skill checks current product and pricing pages, then uses independent reviews and
community sources for complaints and customer perception. The report contains a market
map or competitive matrix, gaps, recommended next steps, and annotated sources. Claims
supplied by the user remain unverified until a source supports them.

### Technology advisor

Use [`tech-advisor`](skills/tech-advisor/) to decide whether to adopt a technology or
which product to buy. A maturity assessment checks the exact technology and version for
production use, ecosystem support, governance, release stability, documentation, and
the roadmap. It ends with an `ADOPT`, `TRIAL`, `ASSESS`, or `HOLD` rating and states what
would change that rating.

A product comparison checks current models against the user's region, budget,
must-haves, compatibility needs, and risk tolerance. It verifies specifications and
prices, chooses a winner, explains the tradeoffs and total cost, and names the best
alternative for a different priority.

### Geopolitical analyst

Use [`geopolitical-analyst`](skills/geopolitical-analyst/) to assess a country, conflict,
alliance, policy, or disputed geopolitical claim. It checks the basic facts, tests key
claims against independent sources, and applies only the frameworks that help explain
the case. It marks important judgments and forecasts with confidence levels, gives the
strongest competing explanation, and states what evidence would change its conclusion.

The answer leads with the judgment and the evidence behind it. It then explains the
causal mechanism, uncertainty, implications, needed context, and signs to watch. The
skill can also audit an article's geopolitical argument or build conditional scenarios.

## How search works

The skills prefer tools in this order:

1. Existing MCP search/fetch tools, if your agent already has them.
2. Built-in agent web search/fetch tools.
3. The packaged Web Forager CLI through `uvx`.
4. A direct `ddgs` fallback through `uv run --no-project`.

Python 3.10-3.13 is supported. Python 3.14 is not supported yet, so all documented
`uvx` commands pin `--python ">=3.10,<3.14"`.

## Optional: MCP server

Use the MCP server only if you want reusable search/fetch tools exposed directly to
an MCP-compatible client. Skills work without this setup.

Add a local stdio MCP server with this standard config:

```json
{
  "mcpServers": {
    "web-forager": {
      "command": "uvx",
      "args": ["--python", ">=3.10,<3.14", "web-forager", "serve"]
    }
  }
}
```

Some clients use a different top-level config shape, but the command and args are
the same.

## Optional: CLI

Run commands without installing the package:

```bash
uvx --python ">=3.10,<3.14" web-forager search "your search query" --max-results 5 --output-format text
uvx --python ">=3.10,<3.14" web-forager news "your topic" --max-results 10 --output-format text
uvx --python ">=3.10,<3.14" web-forager fetch "https://example.com" --format markdown
```

Or install locally:

```bash
uv pip install web-forager
web-forager search "your search query"
web-forager news "your topic"
web-forager fetch "https://example.com"
```

## MCP tools

The MCP server exposes:

| Tool | Purpose |
| --- | --- |
| `duckduckgo_search` | Search the web with DuckDuckGo-compatible results |
| `duckduckgo_news_search` | Search recent news with dates and sources |
| `web_fetch` | Fetch a URL and return markdown or JSON |

Search and news tools return JSON by default and support `output_format="text"` for
LLM-friendly formatted results.

## Development

```bash
git clone https://github.com/CyranoB/web-forager.git
cd web-forager
uv pip install -e ".[dev]"
pytest
```

Useful local commands:

```bash
web-forager serve
web-forager version --debug
```

## Notes

- Search and news search use the `ddgs` package.
- Fetch tries direct HTTP plus `trafilatura` first, then falls back to Jina Reader
  for JavaScript-heavy or bot-protected pages.
- The plugin marketplace manifest lives in `.claude-plugin/marketplace.json`.

## License

MIT. See [LICENSE](LICENSE).

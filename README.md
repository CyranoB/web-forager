# Web Forager

![Illustration of a determined scribe wielding a giant quill fighting a tangle of papers and monsters, with a duck in a cap at his side and stacks of documents and crates behind](assets/header.png)

[![PyPI](https://img.shields.io/pypi/v/web-forager?style=flat-square)](https://pypi.org/project/web-forager/)
[![Python Version](https://img.shields.io/pypi/pyversions/web-forager?style=flat-square)](https://pypi.org/project/web-forager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/web-forager/month)](https://pepy.tech/project/web-forager)
[![skills.sh](https://skills.sh/b/CyranoB/web-forager)](https://skills.sh/CyranoB/web-forager)

*The thing about information on the web is that it doesn't want to be found. It wants to hide behind cookie banners, keep itself to itself, and generally behave like a cat that knows it's time for the vet. Web Forager is the sort of dogged, slightly grubby assistant who goes out there anyway, accompanied by a duck of questionable temperament, rummages through DuckDuckGo, grabs pages directly when it can, and calls in Jina Reader when things get complicated. The results come back neatly converted for LLM consumption, which is to say, in a format that would make a librarian weep with either joy or despair, depending on the librarian.*

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

Use [`article-audit`](skills/article-audit/) when you want to evaluate an article as a
whole rather than verify one isolated statement. The skill reads the complete article,
identifies 4-8 claims that carry its argument, and independently searches for evidence
that supports and challenges each claim. It also checks whether quoted sources have a
material interest, looks for credible voices the article omits, and tests important
numbers or forecasts against denominators, base rates, comparisons, and track records.

The report includes a bottom line, a verdict for every audited claim, missing voices,
scale and context, an overall framing assessment, and sources annotated by their role.
Verdicts range from `CONFIRMED` to `FALSE`; the separate framing judgment can identify
an article whose individual facts are accurate but whose presentation is promotional,
one-sided, or materially misleading. Use [`fact-check`](skills/fact-check/) instead when
you only need to verify a single claim.

### Geopolitical analyst

Use [`geopolitical-analyst`](skills/geopolitical-analyst/) for current assessments of
countries, conflicts, alliances, foreign policy, geoeconomics, and disputed geopolitical
claims. It establishes a factual baseline, tests consequential claims through independent
evidence, and uses the smallest useful set of international-relations or strategic
frameworks. Material inferences and forecasts include calibrated confidence, the strongest
competing explanation, and the evidence that would change the assessment.

The skill puts the judgment first, followed by its decisive evidence and causal mechanism,
uncertainty, implications, essential context, and reassessment indicators. It can also audit
an article's geopolitical argument or build conditional scenarios when future paths are
central to the question.

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

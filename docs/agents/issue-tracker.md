# Issue tracker: GitHub

Issues and specs live in `CyranoB/web-forager` on GitHub. Use the `gh` CLI with
`--repo CyranoB/web-forager` explicitly, including when working in a private clone.

## Conventions

- Create: `gh issue create --repo CyranoB/web-forager --title "..." --body-file <path>`.
- Read the full issue and comments: `gh issue view <number> --repo CyranoB/web-forager --json number,title,body,labels,comments`.
- List: `gh issue list --repo CyranoB/web-forager --state open --json number,title,body,labels`; filter by state and label as needed.
- Comment: `gh issue comment <number> --repo CyranoB/web-forager --body-file <path>`.
- Label: `gh issue edit <number> --repo CyranoB/web-forager --add-label "..."` or `--remove-label "..."`.
- Close: `gh issue close <number> --repo CyranoB/web-forager`.

Save multiline descriptions and comments in a UTF-8 file and pass `--body-file`.
For triage roles, use `docs/agents/triage-labels.md`.

## Pull requests as a triage surface

**PRs as a request surface: no.**

GitHub shares issue and PR numbers. For an ambiguous reference, try
`gh pr view <number> --repo CyranoB/web-forager`, then fall back to `gh issue view`.

## Skill instructions

"Publish to the issue tracker" means create a GitHub issue in this repository.
"Fetch the relevant ticket" means read its body, labels, and comments.

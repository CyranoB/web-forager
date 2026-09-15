# Versions and releases

## Shared skills plugin

The seven skills ship as one plugin for Claude Code and Codex. The canonical
release version is `version` in `.claude-plugin/plugin.json`. The marketplace's
`metadata.version` and `plugins[].version` mirror it for client compatibility.
Individual skills have no release version; Git history records their changes.

For a change under `skills/` or `.claude-plugin/`, choose a new `major.minor.patch`
version and update all three fields together:

```bash
python scripts/plugin_version.py bump 1.1.5
python scripts/plugin_version.py check --base origin/main
```

The version above is an example. Choose a version greater than the current one:
patch for corrections, minor for added capabilities, major for breaking changes.
CI compares against the PR base and rejects plugin changes without a higher
version. If another plugin release merges first, rebase and bump again.

Both clients use the same repository marketplace. Publishing a Git change and
refreshing an installed plugin are separate operations; installed caches may
still contain an earlier revision. An OpenAI public-directory submission is also
a separate distribution step.

## Python package

The MCP server and CLI use their own version line, derived by `setuptools_scm`
from Git tags such as `v3.0.1`. Plugin-only releases do not need a Python tag.
Dependency pins and evaluation/lockfile schema versions are separate from both
release lines.

`src/web_forager/_version.py` is generated during installation/build and ignored
by Git. After switching revisions, refresh the editable installation:

```bash
uv pip install --no-deps -e .
web-forager version
```

An untagged build uses the configured post-release scheme. A Python release
uses a `vMAJOR.MINOR.PATCH` tag and a GitHub release; the publish workflow builds
that tag and supplies its version to `setuptools_scm`. Review and authorize that
release separately from merging a plugin change.

Docker excludes Git metadata, so supply the Python package version explicitly:

```bash
docker build --build-arg VERSION=3.0.1 -t web-forager:3.0.1 .
```

Use the matching release checkout when building that image. Omitting `VERSION`
fails the build instead of silently producing a package labeled `0.0.0`.

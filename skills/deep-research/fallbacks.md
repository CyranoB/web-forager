# Search fallback

Use this route only when a suitable session search tool is unavailable. Run the exactly
pinned `ddgs` package without changing the current project environment:

```bash
uv run --no-project --python '>=3.10,<3.14' --with 'ddgs==9.5.2' python - <<'PY'
from ddgs import DDGS
results = DDGS().text(query="your query", max_results=8)
for r in results:
    print(r["title"], r["href"], r["body"])
PY
```

The workflow requires both search and fetch. If fetching is unavailable, report the
missing capability and resulting evidence gap. Base conclusions only on sources read in
full.

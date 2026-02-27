# bush

## Scope
Build a minimal markdown tree editor with:
- Python API in `bush/back`.
- Vanilla JS web UI in `bush/view`.
- Python deps managed with `uv`.
- Web deps managed with `npm`.
- Minimal files, minimal deps, minimal comments.
- No async code in Python or JS.

## Product requirements
- Browse a rooted tree of markdown files.
- Open and edit markdown files in the browser.
- Save edits through the API.
- Keep notes in `bush/idea` and `bush/plan`.
- Next phase: read log files and support live tailing.

## Repo conventions
- Keep docs short and task-focused.
- Prefer plain markdown and short sections.
- Put implementation plans in `bush/plan/*.md`.
- Put idea notes in `bush/idea/*.md`.

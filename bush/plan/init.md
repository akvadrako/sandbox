# Initial implementation plan

## Goal
Deliver a minimal local web app that lets a user browse a markdown file tree, open files, edit content, and save changes. Use Python + uv for the API and VanJS + npm for the web UI.

## Scope guard
- Do not modify files outside `bush/`.
- Keep all docs, plans, API, and web changes under `bush/*`.
- Follow `bush/README.md` conventions.

## Target structure
- `bush/back`
  - `pyproject.toml`
  - `app.py`
  - `README.md` (run notes, minimal)
- `bush/view`
  - `package.json`
  - `vite.config.js` (only if needed)
  - `index.html`
  - `main.js`
  - `styles.css`
- `bush/idea`
  - optional notes
- `bush/plan`
  - this plan

## Runtime design
1. Python API uses the standard library `http.server` (plain HTTP server) with JSON endpoints.
2. API works against a configured root directory and only allows access under that root.
3. Vite serves the web app during development.
4. Web UI uses VanJS to render and update the tree/editor.
5. All operations are synchronous (no async/await in code).

## Minimal dependency plan
- Python: no web framework; use standard library server.
- JS: VanJS runtime dependency.
- Tooling: Vite for local web serving.
- Keep npm usage to minimal scripts + lockfile.

## API plan (`bush/back`)
1. Create `pyproject.toml` managed by uv.
2. Implement `app.py` with endpoints:
   - `GET /api/tree` -> recursive markdown file tree.
   - `GET /api/file?path=...` -> markdown content.
   - `PUT /api/file` -> save markdown content.
3. Add path validation:
   - Normalize requested path.
   - Reject path traversal.
   - Allow only `.md` files for edit endpoints.
4. Return simple JSON error objects and status codes.
5. Add local run command via uv.

## Web plan (`bush/view`)
1. `index.html` with two panes:
   - Left: tree list.
   - Right: filename, textarea editor, save button, status line.
2. `main.js`:
   - Build UI and bindings with VanJS.
   - Load tree from `/api/tree`.
   - Open selected file via `/api/file`.
   - Save via `PUT /api/file`.
   - Show basic success/error messages.
3. `styles.css` minimal layout and readable editor.
4. `package.json` scripts for Vite (`dev`, `build`, `preview`).

## Integration plan
1. Run API and Vite as separate local processes for development.
2. Configure Vite proxy to route `/api` calls to the Python API.
3. Confirm create/read/update behavior on sample markdown files.

## Validation plan
1. Manual checks:
   - Tree loads.
   - File opens.
   - Edit persists.
   - Traversal blocked.
2. Optional minimal tests (sync only):
   - Unit test path guard.
   - API smoke tests for success + failure cases.

## Phase 2 plan: logs + live tailing
1. Add read-only log browser endpoint (`GET /api/logs/tree`, `GET /api/log` with offsets).
2. Implement polling-based tailing in UI (`setInterval`), not websocket/async.
3. Add file size + incremental read support in API to avoid full reload.
4. Add UI mode switch between markdown editor and log viewer.
5. Enforce stricter size limits and rate limits for log reads.

## Delivery sequence
1. Scaffold backend with uv.
2. Scaffold frontend with Vite + VanJS.
3. Implement markdown tree + open/save loop.
4. Add safety checks and minimal tests.
5. Document run commands in `bush` docs.
6. Start phase 2 (logs) after markdown editing is stable.

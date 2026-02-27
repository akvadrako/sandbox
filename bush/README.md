# bush

## Scope
- Work only under `bush/*`.
- API code in `bush/back`.
- Web code in `bush/view`.
- Notes in `bush/idea` and `bush/plan`.

## Stack
- Python API with `uv` + plain `http.server`.
- Client with VanJS.
- Frontend tooling with `npm` + Vite.
- Keep code minimal and synchronous.

## Features
- Browse and edit markdown files.
- Browse and read log files with polling tail mode.

## Run
- API: `cd bush/back && uv run python app.py --root .. --port 8000`
- Web: `cd bush/view && npm install && npm run dev`

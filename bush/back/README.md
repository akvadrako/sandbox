# back

```bash
uv run python app.py --root .. --port 8000
```

```bash
uv run --with pytest pytest app.py
```

API:
- `GET /api/tree`
- `GET /api/file?path=...`
- `PUT /api/file`
- `GET /api/logs/tree`
- `GET /api/log?path=...&offset=0&limit=4096`

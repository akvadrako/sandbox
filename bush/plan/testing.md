# Testing plan

## Python server unit tests
1. Run `uv run --with pytest pytest app.py` in `bush/back`.
2. Validate path safety and API read/write behavior.

## VanJS Playwright tests
1. Run `npm install` in `bush/view`.
2. Run `npx playwright install --with-deps chromium` once.
3. Run `npm run test:e2e` in `bush/view`.
4. Validate markdown file open and save flow in the browser.

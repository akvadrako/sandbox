# sdlang CLI testsuite

This testsuite uses **one file per test case** under `suite/`.

## Layout

Each file (for example `suite/parse-basic.txt`) is split with `::::` headings, with blank lines around sections for readability:

- `:::: mode` (`parse` or `serialize`)
- `:::: input`
- `:::: transform`
- `:::: output`

Example:

```txt
:::: mode
parse

:::: input
person "Ada"

:::: transform
strip

:::: output
person "Ada"
```

## Run with your real CLI

```bash
uv run sdlang/testsuite/run_tests.py \
  --parse-cmd 'sdlang-cli parse {input}' \
  --serialize-cmd 'sdlang-cli serialize {input}'
```

## Run with the included dummy CLI

```bash
uv run sdlang/testsuite/run_tests.py \
  --parse-cmd 'uv run sdlang/testsuite/dummy_sdlang_cli.py parse {input}' \
  --serialize-cmd 'uv run sdlang/testsuite/dummy_sdlang_cli.py serialize {input}'
```

List discovered tests:

```bash
uv run sdlang/testsuite/run_tests.py --list
```

## Supported transforms

- `identity`
- `strip`
- `collapse-whitespace`
- `lowercase`

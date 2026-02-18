# sdlang CLI testsuite

This testsuite uses **one file per test case** under `suite/`.

## Layout

Each file (for example `suite/parse-basic.txt`) is split with `::::` headings:

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

## Run

```bash
python sdlang/testsuite/run_tests.py \
  --parse-cmd 'sdlang-cli parse {input}' \
  --serialize-cmd 'sdlang-cli serialize {input}'
```

List discovered tests:

```bash
python sdlang/testsuite/run_tests.py --list
```

## Supported transforms

- `identity`
- `strip`
- `collapse-whitespace`
- `lowercase`

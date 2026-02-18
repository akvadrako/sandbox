# sdlang CLI testsuite

This directory contains a small, file-based testsuite for exercising an sdlang CLI.

## Layout

Each case has three files:

- `input.txt` - input passed to the CLI command.
- `transform.txt` - normalization steps applied to both actual and expected output.
- `output.txt` - expected CLI stdout after transforms.

Cases are grouped by mode:

- `tests/parse/<case>/...`
- `tests/serialize/<case>/...`

## Run

```bash
python sdlang/testsuite/run_tests.py \
  --parse-cmd 'sdlang-cli parse {input}' \
  --serialize-cmd 'sdlang-cli serialize {input}'
```

To see all discovered tests:

```bash
python sdlang/testsuite/run_tests.py --list
```

## Supported transforms

One per line in `transform.txt`:

- `identity`
- `strip`
- `collapse-whitespace`
- `lowercase`

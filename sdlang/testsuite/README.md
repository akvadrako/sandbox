# SDLang CLI Test Suite

This folder contains a lightweight fixture-based test suite for validating an SDLang CLI.

## Layout

Each test case is a directory under `tests/` with three text files:

- `input.txt` - SDLang input text
- `transform.txt` - expected parse transformation output
- `output.txt` - expected serialized SDLang output

Current sample cases:

- `tests/basic`
- `tests/list_values`

## Run

```bash
python3 sdlang/testsuite/run_tests.py --cli sdlang
```

By default, the runner uses:

- parse command: `{cli} parse {input}`
- serialize command: `{cli} serialize {transform}`

You can override commands if your CLI syntax is different:

```bash
python3 sdlang/testsuite/run_tests.py \
  --cli ./bin/sdlang \
  --parse-cmd "{cli} parse-file {input}" \
  --serialize-cmd "{cli} write {transform}"
```

The runner compares stdout from each command against the expected fixture text.

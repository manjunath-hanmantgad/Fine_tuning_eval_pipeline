# Quality Standards — Fine-Tuning & Evaluation Pipeline

## Every script must have
- [ ] `argparse` CLI with `--help` that exits 0
- [ ] Input validation before processing begins
- [ ] Meaningful error messages with context (not raw stack traces) for bad input
- [ ] Exit code 0 on success, non-zero on failure
- [ ] `logging` module for warnings/errors — no bare `print()` for errors
- [ ] Unit test for the main success path
- [ ] Unit test for at least one failure/edge case path

## JSONL handling rules
- Open files with `encoding='utf-8'`
- Handle `json.JSONDecodeError` per line, not for the whole file
- Include line numbers in all error messages
- Skip and warn on bad lines — do not abort the whole file

## Output files
- Always write to `outputs/` directory
- Never overwrite without an explicit `--overwrite` flag
- Include a UTC timestamp in auto-generated output filenames

## Prohibited patterns
- No hardcoded file paths
- No `print()` for warnings or errors — use `logging.warning()` / `logging.error()`
- No bare `except:` — catch specific exception types
- No global mutable state
- No API keys in source code or test fixtures

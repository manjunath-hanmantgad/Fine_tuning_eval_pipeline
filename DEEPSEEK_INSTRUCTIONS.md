# DeepSeek Working Instructions
# Fine-Tuning & Evaluation Pipeline

Read this file completely before writing a single line of code.

---

## What this project is

A local-first fine-tuning evaluation pipeline. It does NOT train a model.
It validates data quality, exports datasets in training-ready formats, runs a
baseline model evaluation, and produces a before/after comparison report.

The demo goal: run the full pipeline on `data/sample_instructions.jsonl` and
show a diagnostics report + eval comparison table.

---

## What has already been built (do not rewrite these)

| File | Status | What it does |
|------|--------|--------------|
| `data/sample_instructions.jsonl` | Done | 25 instruction/response pairs, Alpaca format |
| `scripts/validate_dataset.py` | Done | Schema, length, duplicate checks |
| `scripts/diagnostics.py` | Done | Stats, token estimates, quality flags |
| `scripts/export_finetune.py` | Done | Converts to openai / anthropic / alpaca format |
| `eval/baseline_eval.py` | Done | Calls Claude API, saves responses |
| `eval/compare_report.py` | Done | Jaccard overlap before/after comparison |
| `tests/test_validate_dataset.py` | Done | 12 unit tests |
| `tests/test_diagnostics.py` | Done | 11 unit tests |
| `tests/test_export_finetune.py` | Done | 10 unit tests |
| `conftest.py` | Done | Adds project root to sys.path for test imports |
| `requirements.txt` | Done | `anthropic`, `pytest` |

---

## Your tasks (in order — do not skip ahead)

### TASK-01: Verify the test suite
```bash
pip install -r requirements.txt
pytest tests/ -v
```
Expected: all tests green.
If any test fails: read the error, find the bug in the relevant script, fix it,
re-run. Do not modify test logic to make tests pass — fix the source.

---

### TASK-02: Smoke test the full local pipeline
Run these commands in order:
```bash
python scripts/validate_dataset.py data/sample_instructions.jsonl
python scripts/diagnostics.py data/sample_instructions.jsonl
python scripts/export_finetune.py data/sample_instructions.jsonl --format openai
python scripts/export_finetune.py data/sample_instructions.jsonl --format anthropic
python scripts/export_finetune.py data/sample_instructions.jsonl --format openai --split 0.2
```
All five must exit 0. Check `outputs/` for generated files.
Fix any runtime errors you find. Update tests if you fix a bug.

---

### TASK-03: Smoke test the eval harness (skip if no API key)
If you have `ANTHROPIC_API_KEY` set:
```bash
python eval/baseline_eval.py data/sample_instructions.jsonl --max-records 3
# note the filename it prints, then:
cp outputs/eval_*.jsonl outputs/eval_before.jsonl
python eval/baseline_eval.py data/sample_instructions.jsonl --max-records 3 \
    --output outputs/eval_after.jsonl
python eval/compare_report.py outputs/eval_before.jsonl outputs/eval_after.jsonl
```
Fix any errors found.

---

### TASK-04: Edge case hardening
Test and fix these specific cases:
1. `python scripts/validate_dataset.py /nonexistent/file.jsonl`
   → Must print error, exit non-zero, no stack trace
2. Create a file with only blank lines and run validate_dataset.py on it
   → Must handle gracefully
3. `python scripts/export_finetune.py data/sample_instructions.jsonl --split 0.9`
   → Must reject with clear error (out of range)
4. Run export_finetune.py twice in a row without `--overwrite`
   → Second run must refuse with clear error

For each case that does not already behave correctly: fix the script and add a test.

---

### TASK-05: Demo shell script
Create `scripts/run_demo.sh` that runs the full local pipeline end-to-end.
It must work without an API key (skip eval step).

```bash
#!/usr/bin/env bash
set -e

echo "=== Fine-Tuning Evaluation Pipeline Demo ==="
python scripts/validate_dataset.py data/sample_instructions.jsonl
python scripts/diagnostics.py data/sample_instructions.jsonl
python scripts/export_finetune.py data/sample_instructions.jsonl --format openai --overwrite
echo ""
echo "Demo complete. Check outputs/ for generated files."
```
Expand this with any useful printed context. Test it with `bash scripts/run_demo.sh`.

---

## Rules you must follow

1. **One task at a time.** Finish TASK-01 completely before starting TASK-02.
2. **Never modify test files to make tests pass.** Fix the source code instead.
3. **Never hardcode file paths.** All paths must come from `argparse` or be relative to the script's working directory.
4. **Never commit API keys.** If you need to test with a real key, use an environment variable.
5. **Use `logging` for errors and warnings.** Do not use `print()` for error output.
6. **If you change a data format** (e.g. fields in a JSONL record), update all scripts that read that format and all affected tests.

---

## Data format reference

### Input (Alpaca format) — `data/sample_instructions.jsonl`
```json
{"instruction": "...", "input": "...", "response": "..."}
```
- `instruction`: required, string, 5–2000 chars
- `input`: optional context, string, may be empty
- `response`: required, string, 10–4000 chars
- `system`: optional system prompt, string

### OpenAI export format
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### Anthropic export format
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}], "system": "..."}
```

### Eval result format (baseline_eval.py output)
```json
{"instruction": "...", "input": "...", "reference": "...", "model_response": "...", "model": "...", "status": "ok"}
```

---

## How to report back to Codex (reviewer in terminal 3)

After completing each task, post a summary in this format:

```
TASK-XX complete
- What ran: <commands>
- Result: PASS / FAIL
- Changes made: <list of files changed>
- Tests added: <list>
- Issues found: <list or "none">
```

---

## Where things live

```
.agent/memory/current-state.md  — update this when you finish a task
.agent/memory/known-issues.md   — add any bugs you find but don't fix
TASKS.md                        — task definitions with acceptance criteria
outputs/                        — all generated files go here (gitignored)
```

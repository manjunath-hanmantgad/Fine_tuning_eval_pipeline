# Task List — Fine-Tuning & Evaluation Pipeline

Ordered by dependency. Complete each task before starting the next.

---

## TASK-01 — Environment setup and test suite verification
**Owner:** DeepSeek  
**Status:** DONE ✅ — 34/34 tests pass, no changes needed

### Steps
1. `pip install -r requirements.txt`
2. `pytest tests/ -v`
3. Fix any import errors or test failures
4. All tests must pass before proceeding

### Acceptance criteria
- `pytest tests/ -v` exits 0 with all tests green
- No import errors in any script

---

## TASK-02 — End-to-end local pipeline smoke test
**Owner:** DeepSeek  
**Status:** DONE ✅ — all 5 commands exit 0, 6 output files confirmed in outputs/

### Steps
Run each command in order and confirm exit code 0:

```bash
python scripts/validate_dataset.py data/sample_instructions.jsonl
python scripts/diagnostics.py data/sample_instructions.jsonl
python scripts/export_finetune.py data/sample_instructions.jsonl --format openai
python scripts/export_finetune.py data/sample_instructions.jsonl --format anthropic
python scripts/export_finetune.py data/sample_instructions.jsonl --format openai --split 0.2
```

### Acceptance criteria
- All five commands exit 0
- `outputs/` contains: diagnostics report (.md) and three export files (.jsonl)
- Validation report prints `Status: PASS`

---

## TASK-03 — Eval harness smoke test (requires API key)
**Owner:** DeepSeek  
**Status:** SKIPPED ⏭ — ANTHROPIC_API_KEY not set; eval harness code is complete, untested live

### Steps
```bash
export ANTHROPIC_API_KEY=<your-key>
python eval/baseline_eval.py data/sample_instructions.jsonl --max-records 3
```
Note the output filename, then run it again to simulate a "before" vs "after":
```bash
cp outputs/eval_*.jsonl outputs/eval_before.jsonl
python eval/baseline_eval.py data/sample_instructions.jsonl --max-records 3 --output outputs/eval_after.jsonl
python eval/compare_report.py outputs/eval_before.jsonl outputs/eval_after.jsonl
```

### Acceptance criteria
- baseline_eval.py exits 0, produces a JSONL file with `"status": "ok"` records
- compare_report.py produces a markdown table with per-record scores
- compare_report.py exits 0

---

## TASK-04 — Edge case hardening (DeepSeek identifies and fixes)
**Owner:** DeepSeek  
**Status:** DONE ✅ — 43/43 tests pass; empty-file bug fixed; UTF-8, CRLF, directory-input edge cases hardened; logging.error() on zero-record path. Codex: APPROVED.

### What to check
- validate_dataset.py with a completely empty file → should print error and exit non-zero
- diagnostics.py with a file containing only blank lines → should error cleanly
- export_finetune.py with `--split 0.5` (out of range) → should error with clear message
- export_finetune.py running twice without `--overwrite` → should refuse and error

Add or update tests in `tests/` for each case found.

### Acceptance criteria
- All edge cases handled with clear error messages (not stack traces)
- Tests added for each new case
- `pytest tests/ -v` still exits 0

---

## TASK-05 — Demo script
**Owner:** DeepSeek  
**Status:** DONE ✅ — scripts/run_demo.sh created; runs full pipeline end-to-end, exit 0, macOS compatible

Create `scripts/run_demo.sh` — a single shell script that runs the full local pipeline
(no API key required, skips eval harness) and prints a summary at the end.

### Acceptance criteria
- `bash scripts/run_demo.sh` runs without errors on a clean clone
- Final output shows: record count, token estimate, validation status, export file paths

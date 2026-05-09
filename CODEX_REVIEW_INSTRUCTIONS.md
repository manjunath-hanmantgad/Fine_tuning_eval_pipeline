# Codex Review Instructions
# Fine-Tuning & Evaluation Pipeline

You are the code reviewer for this project. DeepSeek writes the code; you review it.
Read this file completely before reviewing anything.

---

## Project context (read once)

This is a local-first fine-tuning evaluation pipeline. It does NOT train a model.
It validates data quality, exports training-ready datasets, runs model evaluations,
and produces a before/after comparison report.

Quality standards are defined in `.agent/quality.md`.
Architecture decisions are in `.agent/memory/decisions.md`.

---

## What has already been completed (do not re-review)

- TASK-01: All 34 unit tests pass. No changes were needed.
- TASK-02: Full local pipeline runs clean. 6 output files generated in outputs/.

---

## Remaining tasks DeepSeek will complete

| Task | File DeepSeek will create/modify | Your review trigger |
|------|----------------------------------|---------------------|
| TASK-03 | `eval/baseline_eval.py` (test only, no edits expected) | After DeepSeek reports TASK-03 complete |
| TASK-04 | `scripts/validate_dataset.py`, `scripts/diagnostics.py`, `scripts/export_finetune.py`, `tests/` | After DeepSeek reports TASK-04 complete |
| TASK-05 | `scripts/run_demo.sh` | After DeepSeek reports TASK-05 complete |

**Only review after DeepSeek reports a task complete. Do not pre-review.**

---

## How to review each task

### After TASK-03 — Eval harness smoke test

Check the eval output JSONL in `outputs/`:
- Every record has `"status": "ok"` — flag any with `"status": "error: ..."`
- `model_response` field is non-empty for all passing records
- `instruction` field matches the original `data/sample_instructions.jsonl`
- compare_report.py markdown table renders correctly (pipe-aligned, no broken rows)

**Recommendations to make:**
- Does the Jaccard overlap score feel meaningful? Suggest upgrading to a model-graded score for production (reference `known-issues.md` KI-02).
- Is the `--delay 0.5` between API calls appropriate? Flag if rate limit errors appear in the output.

---

### After TASK-04 — Edge case hardening

For each fix DeepSeek made, check:

1. **No bare `except:`** — every exception catch must name a specific type (`json.JSONDecodeError`, `FileNotFoundError`, `ValueError`, etc.)
2. **Errors use `logging.error()` not `print()`** — check imports at top of each changed file
3. **Exit codes are correct** — non-zero on failure, 0 on success
4. **Error message includes enough context** — must say what failed and why, not just "error"
5. **New tests are in `tests/`** — one test per edge case fixed
6. **`pytest tests/ -v` still exits 0** — run it yourself to confirm

**Recommendations to make:**
- Are there any edge cases DeepSeek missed? Common ones: file is a directory not a file, file has Windows line endings (CRLF), file encoding is not UTF-8.
- Is there a missing `--dry-run` flag for export_finetune.py? (Would be useful to preview conversion without writing files.)

---

### After TASK-05 — Demo script

Review `scripts/run_demo.sh`:

1. **First line is `#!/usr/bin/env bash`** and `set -e` is present (stops on first error)
2. **All paths are relative** — no hardcoded absolute paths like `/Users/...`
3. **Uses `--overwrite` flag** on export commands so the script is re-runnable
4. **Prints a readable summary** at the end — record count, token estimate, list of output files
5. **Run it yourself:** `bash scripts/run_demo.sh` — must exit 0 on a fresh run and again on a second run
6. **No API key required** — eval step must be skipped or clearly marked optional

**Recommendations to make:**
- Should the script print timestamps so the user can see how long each step takes?
- Should it print the diagnostics report content inline rather than just a file path?
- Is there a `--help` or usage line at the top of the script?

---

## How to report your findings

After reviewing each task, report in this format:

```
TASK-XX Review complete
Verdict: APPROVED / APPROVED WITH SUGGESTIONS / NEEDS FIXES

Issues (must fix before task is marked done):
- <file>:<line> — <what is wrong and why>

Suggestions (improvements, not blockers):
- <suggestion with reasoning>

Questions for the team:
- <anything that needs a decision>
```

If verdict is **NEEDS FIXES**: DeepSeek must fix the listed issues and re-submit for review.
If verdict is **APPROVED WITH SUGGESTIONS**: DeepSeek may implement suggestions at their discretion.
If verdict is **APPROVED**: Task is done. Update `TASKS.md` status to DONE ✅.

---

## Standing quality rules (apply to every review)

From `.agent/quality.md` — reject any code that violates these:

| Rule | What to check |
|------|--------------|
| No bare `except:` | `grep -n "except:" <file>` must return nothing |
| No hardcoded paths | `grep -rn "/Users/" scripts/ eval/` must return nothing |
| No `print()` for errors | All warnings/errors go through `logging` |
| Exit code correctness | `sys.exit(1)` on failure, `sys.exit(0)` on success |
| UTF-8 file opens | All `open()` calls have `encoding='utf-8'` |
| No API keys in source | `grep -rn "sk-ant" scripts/ eval/ tests/` must return nothing |

---

## Proactive recommendations (make these even if not asked)

After TASK-05 is complete and all tasks are done, give the team a final recommendation on:

1. **Demo readiness:** Is the pipeline ready to show to a client? What would you add for a stronger demo?
2. **Test coverage gaps:** Are there untested code paths that matter? (e.g. the `--split` logic, `--overwrite` behavior)
3. **Public release checklist:** What should be done before pushing this to a public repo? (secrets scan, README update, LICENSE file, example output screenshots for demo/README.md)

# Boot Instructions — Fine-Tuning & Evaluation Pipeline

Project: SKIP-07-finetuning-evaluation-pipeline
Goal: Dataset quality checks + before/after evaluation report. Training is optional.

## Check before starting
1. `git branch --show-current` — confirm you are on the right branch
2. Read `.agent/memory/current-state.md` — see what is already done
3. Read `.agent/rules.md` — understand scope rules
4. Read the active task in `TASKS.md`

## Project structure
```
data/           — JSONL datasets (Alpaca format)
scripts/        — validate_dataset.py, diagnostics.py, export_finetune.py
eval/           — baseline_eval.py, compare_report.py
tests/          — pytest unit tests for all scripts
outputs/        — generated reports and processed files (gitignored)
.agent/         — agent operating instructions and memory
```

## Stack
- Python 3.10+
- No ML dependencies for local mode (validation, diagnostics, export run offline)
- `anthropic` SDK for eval harness (needs ANTHROPIC_API_KEY env var)
- `pytest` for tests

## Demo flow
1. Load `data/sample_instructions.jsonl`
2. `python scripts/validate_dataset.py data/sample_instructions.jsonl`
3. `python scripts/diagnostics.py data/sample_instructions.jsonl`
4. `python scripts/export_finetune.py data/sample_instructions.jsonl --format openai --split 0.1`
5. `python eval/baseline_eval.py data/sample_instructions.jsonl --max-records 5`
6. `python eval/compare_report.py outputs/eval_before.jsonl outputs/eval_after.jsonl`

## Environment variables required for eval
- `ANTHROPIC_API_KEY` — for baseline_eval.py only

# Changelog

## v0.1.0 — Initial Pipeline

### Features

- **Dataset validation** (`scripts/validate_dataset.py`)
  - Schema, field-length, and duplicate checks for JSONL datasets in Alpaca format
  - Clear error reporting via logging module, non-zero exit codes on failure
  - Edge-case hardening: empty files, non-UTF-8 input, directory-as-path, blank lines

- **Dataset diagnostics** (`scripts/diagnostics.py`)
  - Token estimation (word-count heuristic), length statistics (min/max/mean/median/std/p90/p99), quality flags
  - Markdown report written to `outputs/`

- **Fine-tuning export** (`scripts/export_finetune.py`)
  - Converts Alpaca-format JSONL to OpenAI, Anthropic, or Alpaca format
  - Train/validation split with `--split` flag (0.0–0.3) and `--seed` for reproducibility
  - Overwrite protection (`--overwrite` required to replace existing output)
  - `--deduplicate` flag to drop records with duplicate instruction+input pairs

- **Evaluation harness** (`eval/baseline_eval.py` + `eval/compare_report.py`)
  - Baseline evaluation via Anthropic API with configurable model and max records
  - Before/after comparison report using Jaccard overlap scoring (default) or LLM-as-judge (`--llm-judge` flag)

- **Cost estimation** (`scripts/cost_estimate.py`)
  - Token counting with tiktoken (exact) or heuristic fallback
  - Cost table for OpenAI and Anthropic fine-tuning at published rates

- **Training stub** (`scripts/train_stub.py`)
  - Placeholder structure for Hugging Face PEFT LoRA fine-tuning
  - `--dry-run` mode to validate exported JSONL format compatibility

- **Azure integration stubs** (`azure/`)
  - `azure/upload_dataset.py` — stub for uploading exported datasets to Azure Blob Storage
  - `azure/deploy_endpoint.py` — stub for deploying fine-tuned models to Azure ML endpoints
  - `azure/README.md` — credentials guide and architecture overview

### Infrastructure

- CI pipeline (`.github/workflows/ci.yml`):
  - Quality gate: bare-except check, hardcoded-path check, secrets scan
  - Test matrix: Python 3.9, 3.10, 3.11, 3.12
  - CLI negative-path smoke tests (empty-file validate, out-of-range split)
  - Demo integration test (`bash scripts/run_demo.sh`)
- Demo script (`scripts/run_demo.sh`) — single-command end-to-end walkthrough
- Demo artifact (`demo/sample_output.txt`) — sample terminal output

### What this project does NOT do

- Does not train or fine-tune any model
- Does not host or serve any model
- Does not require cloud credentials or GPU hardware

# Architecture Decisions

## ADR-01: Alpaca format as canonical internal format
**Decision:** All dataset files use Alpaca format `{instruction, input, response}` internally.
**Why:** Simplest format, widely understood, easy to convert to any target (OpenAI/Anthropic).
**Consequence:** export_finetune.py handles all format conversions at export time.

## ADR-02: No ML dependencies for local pipeline
**Decision:** validate_dataset.py, diagnostics.py, export_finetune.py have zero ML dependencies.
**Why:** Demo must run without GPU or cloud credentials. Token estimates use word-count heuristic.
**Consequence:** Token counts are approximate (~word_count × 1.3). Good enough for diagnostics.

## ADR-03: Anthropic SDK for eval harness, not OpenAI
**Decision:** baseline_eval.py uses the Anthropic SDK (claude-haiku-4-5-20251001 default).
**Why:** Project is in an Anthropic-focused portfolio. Haiku is cheapest for bulk eval runs.
**Consequence:** Requires ANTHROPIC_API_KEY. Eval can be skipped for offline demo.

## ADR-04: Jaccard word overlap as baseline score
**Decision:** compare_report.py uses Jaccard similarity between response and reference word sets.
**Why:** Zero dependencies, reproducible, good enough for a before/after comparison demo.
**Consequence:** Does not capture semantic quality. Flag in report for production upgrade path.

## ADR-05: outputs/ directory is gitignored
**Decision:** All generated files (reports, exports, eval results) go to outputs/ and are gitignored.
**Why:** Prevents accidental commits of large eval result files or API responses.
**Consequence:** outputs/ must be re-generated after a fresh clone. outputs/.gitkeep tracks the dir.

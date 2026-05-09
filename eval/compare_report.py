#!/usr/bin/env python3
"""Compare two eval result files and generate a before/after report."""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

OUTPUTS_DIR = Path("outputs")


def load_eval_results(path: Path) -> list[dict]:
    results = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning(f"Line {line_num}: skipping invalid JSON")
    return results


def jaccard_score(text_a: str, text_b: str) -> float:
    """Jaccard similarity between word sets of two strings."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    union = words_a | words_b
    if not union:
        return 0.0
    return round(len(words_a & words_b) / len(union), 4)


def score_record(record: dict) -> dict:
    response = record.get("model_response", "")
    reference = record.get("reference", "")
    return {
        "overlap": jaccard_score(response, reference) if reference else 0.0,
        "length_ratio": round(len(response) / len(reference), 2) if reference else 0.0,
        "has_content": bool(response.strip()),
        "response_len": len(response),
    }


def align_pairs(before: list[dict], after: list[dict]) -> list[tuple[dict, dict]]:
    after_index = {r["instruction"]: r for r in after}
    pairs = []
    for b in before:
        key = b["instruction"]
        if key in after_index:
            pairs.append((b, after_index[key]))
        else:
            log.warning(f"No matching 'after' record for: {key[:60]}...")
    return pairs


def avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def generate_report(pairs: list[tuple[dict, dict]], before_label: str, after_label: str) -> str:
    b_scores = [score_record(b) for b, _ in pairs]
    a_scores = [score_record(a) for _, a in pairs]

    b_overlap_avg = avg([s["overlap"] for s in b_scores])
    a_overlap_avg = avg([s["overlap"] for s in a_scores])
    b_len_avg = avg([s["length_ratio"] for s in b_scores])
    a_len_avg = avg([s["length_ratio"] for s in a_scores])

    lines = [
        "# Before/After Evaluation Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Before: `{before_label}`",
        f"After:  `{after_label}`",
        f"Matched pairs: {len(pairs)}",
        "",
        "## Aggregate Scores",
        "",
        "| Metric | Before | After | Delta |",
        "|--------|--------|-------|-------|",
        f"| Word overlap (Jaccard) | {b_overlap_avg} | {a_overlap_avg} | {a_overlap_avg - b_overlap_avg:+.4f} |",
        f"| Length ratio vs ref    | {b_len_avg} | {a_len_avg} | {a_len_avg - b_len_avg:+.4f} |",
        "",
        "## Per-Record Comparison",
        "",
        "| # | Instruction (truncated) | Before | After | Delta |",
        "|---|------------------------|--------|-------|-------|",
    ]

    for i, ((b, a), bs, as_) in enumerate(zip(pairs, b_scores, a_scores), 1):
        inst = b["instruction"][:50].replace("|", "/")
        delta = round(as_["overlap"] - bs["overlap"], 4)
        lines.append(f"| {i} | {inst}… | {bs['overlap']} | {as_['overlap']} | {delta:+.4f} |")

    lines += [
        "",
        "## Notes",
        "- **Word overlap** uses Jaccard similarity between response and reference word sets.",
        "- **Length ratio** > 1.0 means model response is longer than the reference.",
        "- **Positive delta** indicates improvement after the change being evaluated.",
        "- This is a lexical metric — for production, replace with a model-graded quality score.",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two eval result files (before/after).")
    parser.add_argument("before", type=Path, help="Before eval results JSONL")
    parser.add_argument("after", type=Path, help="After eval results JSONL")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output report path (default: outputs/compare_<timestamp>.md)")
    args = parser.parse_args()

    for p in (args.before, args.after):
        if not p.exists():
            log.error(f"File not found: {p}")
            sys.exit(1)

    before = load_eval_results(args.before)
    after = load_eval_results(args.after)

    if not before or not after:
        log.error("One or both input files have no valid records")
        sys.exit(1)

    pairs = align_pairs(before, after)
    if not pairs:
        log.error("No matching records found between before and after files")
        sys.exit(1)

    report = generate_report(pairs, str(args.before), str(args.after))

    OUTPUTS_DIR.mkdir(exist_ok=True)
    if args.output:
        out_path = args.output
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUTS_DIR / f"compare_{ts}.md"

    out_path.write_text(report, encoding="utf-8")
    log.info(f"Report written to {out_path}")
    print(report)


if __name__ == "__main__":
    main()

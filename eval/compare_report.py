#!/usr/bin/env python3
"""Compare before/after evaluation responses and produce a side-by-side report."""

from __future__ import annotations

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


LLM_JUDGE_PROMPT = """You are an evaluator. Rate the following response to the given instruction on a scale of 1-5 for helpfulness and accuracy.
Instruction: {instruction}
Response: {model_response}
Reference answer: {reference}
Reply with only a single integer 1-5."""


def _llm_judge_score(instruction: str, model_response: str, reference: str) -> int:
    """Call the Anthropic API to grade a response 1–5. Returns 0 on error."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": LLM_JUDGE_PROMPT.format(
                    instruction=instruction,
                    model_response=model_response,
                    reference=reference,
                ),
            }],
        )
        text = msg.content[0].text.strip()
        return max(1, min(5, int(text)))
    except Exception as e:
        log.warning(f"LLM judge call failed: {e}")
        return 0


def score_record_llm(record: dict) -> dict:
    instruction = record.get("instruction", "")
    response = record.get("model_response", "")
    reference = record.get("reference", "")
    score = _llm_judge_score(instruction, response, reference)
    return {
        "score": score,
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


def generate_report(pairs: list[tuple[dict, dict]], before_label: str, after_label: str,
                    llm_judge: bool = False) -> str:
    if llm_judge:
        b_scores = [score_record_llm(b) for b, _ in pairs]
        a_scores = [score_record_llm(a) for _, a in pairs]
        score_label = "LLM judge (1-5)"
        score_key = "score"
    else:
        b_scores = [score_record(b) for b, _ in pairs]
        a_scores = [score_record(a) for _, a in pairs]
        score_label = "Word overlap (Jaccard)"
        score_key = "overlap"

    b_avg = avg([s[score_key] for s in b_scores])
    a_avg = avg([s[score_key] for s in a_scores])
    b_len_avg = avg([s["length_ratio"] for s in b_scores])
    a_len_avg = avg([s["length_ratio"] for s in a_scores])

    lines = [
        "# Before/After Evaluation Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Before: `{before_label}`",
        f"After:  `{after_label}`",
        f"Matched pairs: {len(pairs)}",
        "Scoring method: " + ("LLM-as-judge (Claude, 1-5 scale)" if llm_judge else "Jaccard word overlap"),
        "",
        "## Aggregate Scores",
        "",
        "| Metric | Before | After | Delta |",
        "|--------|--------|-------|-------|",
        f"| {score_label} | {b_avg} | {a_avg} | {a_avg - b_avg:+.4f} |",
        f"| Length ratio vs ref    | {b_len_avg} | {a_len_avg} | {a_len_avg - b_len_avg:+.4f} |",
        "",
        "## Per-Record Comparison",
        "",
        "| # | Instruction (truncated) | Before | After | Delta |",
        "|---|------------------------|--------|-------|-------|",
    ]

    for i, ((b, a), bs, as_) in enumerate(zip(pairs, b_scores, a_scores), 1):
        inst = b["instruction"][:50].replace("|", "/")
        delta = round(as_[score_key] - bs[score_key], 4)
        lines.append(f"| {i} | {inst}… | {bs[score_key]} | {as_[score_key]} | {delta:+.4f} |")

    if llm_judge:
        lines += [
            "",
            "## Notes",
            "- **LLM judge score** uses Claude to rate each response 1–5 for helpfulness and accuracy against the reference.",
            "- A score of 0 means the API call failed for that record.",
            "- **Length ratio** > 1.0 means model response is longer than the reference.",
            "- **Positive delta** indicates improvement after the change being evaluated.",
        ]
    else:
        lines += [
            "",
            "## Notes",
            "- **Word overlap** uses Jaccard similarity between response and reference word sets.",
            "- **Length ratio** > 1.0 means model response is longer than the reference.",
            "- **Positive delta** indicates improvement after the change being evaluated.",
            "- This is a lexical metric — for production, consider --llm-judge for model-graded quality scoring.",
        ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two eval result files (before/after).")
    parser.add_argument("before", type=Path, help="Before eval results JSONL")
    parser.add_argument("after", type=Path, help="After eval results JSONL")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output report path (default: outputs/compare_<timestamp>.md)")
    parser.add_argument("--llm-judge", action="store_true",
                        help="Use LLM-as-judge (Claude) to score responses 1–5 instead of Jaccard overlap")
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

    report = generate_report(pairs, str(args.before), str(args.after), llm_judge=args.llm_judge)

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

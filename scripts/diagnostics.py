#!/usr/bin/env python3
"""Generate a diagnostics report for a JSONL instruction dataset."""

import argparse
import json
import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

OUTPUTS_DIR = Path("outputs")


def estimate_tokens(text: str) -> int:
    """Rough token estimate using word count × 1.3 (no tiktoken required)."""
    return max(1, round(len(text.split()) * 1.3))


def field_stats(values: list[int]) -> dict:
    if not values:
        return {}
    values = sorted(values)
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return {
        "min": values[0],
        "max": values[-1],
        "mean": round(mean, 1),
        "median": values[n // 2],
        "std": round(math.sqrt(variance), 1),
        "p90": values[int(n * 0.9)],
        "p99": values[min(int(n * 0.99), n - 1)],
    }


def load_records(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning(f"Skipping invalid JSON at line {line_num}")
    return records


def run_diagnostics(records: list[dict]) -> dict:
    instruction_lens = [len(r.get("instruction", "")) for r in records]
    response_lens = [len(r.get("response", "")) for r in records]
    input_lens = [len(r["input"]) for r in records if r.get("input", "").strip()]

    total_tokens = sum(
        estimate_tokens(r.get("instruction", ""))
        + estimate_tokens(r.get("input", ""))
        + estimate_tokens(r.get("response", ""))
        for r in records
    )

    has_input = sum(1 for r in records if r.get("input", "").strip())
    has_system = sum(1 for r in records if r.get("system", "").strip())

    quality_flags: list[str] = []
    for i, r in enumerate(records, 1):
        resp = r.get("response", "")
        inst = r.get("instruction", "")
        if len(resp) < 20:
            quality_flags.append(f"Record {i}: very short response ({len(resp)} chars)")
        if resp.lower().strip() in ("yes", "no", "ok", "sure", "true", "false"):
            quality_flags.append(f"Record {i}: single-word/phrase response — low training signal")
        if len(inst) < 10:
            quality_flags.append(f"Record {i}: very short instruction ({len(inst)} chars)")

    return {
        "total_records": len(records),
        "records_with_input": has_input,
        "records_with_system": has_system,
        "estimated_total_tokens": total_tokens,
        "avg_tokens_per_record": round(total_tokens / len(records), 1) if records else 0,
        "instruction_length": field_stats(instruction_lens),
        "response_length": field_stats(response_lens),
        "input_length": field_stats(input_lens) if input_lens else {},
        "quality_flags": quality_flags,
        "flag_count": len(quality_flags),
    }


def write_report(result: dict, output_path: Path) -> None:
    lines = [
        "# Dataset Diagnostics Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Summary",
        f"- Total records: {result['total_records']}",
        f"- Records with context input: {result['records_with_input']}",
        f"- Records with system prompt: {result['records_with_system']}",
        f"- Estimated total tokens: {result['estimated_total_tokens']:,}",
        f"- Avg tokens per record: {result['avg_tokens_per_record']}",
        "",
        "## Instruction Length (chars)",
    ]
    for k, v in result["instruction_length"].items():
        lines.append(f"- {k}: {v}")

    lines += ["", "## Response Length (chars)"]
    for k, v in result["response_length"].items():
        lines.append(f"- {k}: {v}")

    if result["input_length"]:
        lines += ["", "## Context Input Length (chars)"]
        for k, v in result["input_length"].items():
            lines.append(f"- {k}: {v}")

    lines += ["", f"## Quality Flags ({result['flag_count']} total)"]
    if result["quality_flags"]:
        for flag in result["quality_flags"]:
            lines.append(f"- {flag}")
    else:
        lines.append("- None — dataset looks clean")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Report written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run diagnostics on a JSONL instruction dataset.")
    parser.add_argument("input", type=Path, help="Path to input JSONL file")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output report path (default: outputs/diagnostics_<timestamp>.md)")
    args = parser.parse_args()

    if not args.input.exists():
        log.error(f"File not found: {args.input}")
        sys.exit(1)

    records = load_records(args.input)
    if not records:
        log.error("No valid records found in input file")
        sys.exit(1)

    result = run_diagnostics(records)

    print(f"\nDataset:       {args.input}")
    print(f"Records:       {result['total_records']}")
    print(f"Est. tokens:   {result['estimated_total_tokens']:,}")
    print(f"Quality flags: {result['flag_count']}")

    OUTPUTS_DIR.mkdir(exist_ok=True)
    if args.output:
        out_path = args.output
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUTS_DIR / f"diagnostics_{ts}.md"

    write_report(result, out_path)
    sys.exit(0)


if __name__ == "__main__":
    main()

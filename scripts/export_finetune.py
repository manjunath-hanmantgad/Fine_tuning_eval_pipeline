#!/usr/bin/env python3
"""Export a JSONL instruction dataset to fine-tuning format (OpenAI, Anthropic, or Alpaca)."""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

OUTPUTS_DIR = Path("outputs")


def to_openai_format(record: dict) -> dict:
    messages = []
    if record.get("system"):
        messages.append({"role": "system", "content": record["system"]})
    user_content = record["instruction"]
    if record.get("input"):
        user_content = f"{user_content}\n\n{record['input']}"
    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": record["response"]})
    return {"messages": messages}


def to_anthropic_format(record: dict) -> dict:
    user_content = record["instruction"]
    if record.get("input"):
        user_content = f"{user_content}\n\n{record['input']}"
    result: dict = {
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": record["response"]},
        ]
    }
    if record.get("system"):
        result["system"] = record["system"]
    return result


def to_alpaca_format(record: dict) -> dict:
    return {
        "instruction": record["instruction"],
        "input": record.get("input", ""),
        "response": record["response"],
    }


FORMATTERS = {
    "openai": to_openai_format,
    "anthropic": to_anthropic_format,
    "alpaca": to_alpaca_format,
}


def load_records(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if "instruction" not in record or "response" not in record:
                    log.warning(f"Line {line_num}: skipping record missing required fields")
                    continue
                records.append(record)
            except json.JSONDecodeError:
                log.warning(f"Line {line_num}: skipping invalid JSON")
    return records


def write_jsonl(records: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    log.info(f"Wrote {len(records)} records to {path}")


def deduplicate_records(records: list[dict]) -> list[dict]:
    """Remove records with duplicate (instruction, input) pairs, keeping the first occurrence."""
    seen: set[tuple[str, str]] = set()
    deduped: list[dict] = []
    for r in records:
        key = (r.get("instruction", ""), r.get("input", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def main() -> None:
    parser = argparse.ArgumentParser(description="Export JSONL dataset to fine-tuning format.")
    parser.add_argument("input", type=Path, help="Input JSONL file (Alpaca format)")
    parser.add_argument("--format", choices=list(FORMATTERS), default="openai",
                        help="Output format (default: openai)")
    parser.add_argument("--split", type=float, default=0.0, metavar="VAL_RATIO",
                        help="Validation split ratio 0.0–0.3 (default: 0 = no split)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split (default: 42)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--deduplicate", action="store_true",
                        help="Remove records with duplicate (instruction, input) pairs")
    args = parser.parse_args()

    if not args.input.exists():
        log.error(f"File not found: {args.input}")
        sys.exit(1)

    if not 0.0 <= args.split <= 0.3:
        log.error("--split must be between 0.0 and 0.3")
        sys.exit(1)

    records = load_records(args.input)
    if not records:
        log.error("No valid records loaded")
        sys.exit(1)

    if args.deduplicate:
        before = len(records)
        records = deduplicate_records(records)
        dropped = before - len(records)
        if dropped:
            log.info(f"Removed {dropped} duplicate record(s)")

    formatter = FORMATTERS[args.format]
    converted = [formatter(r) for r in records]

    OUTPUTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"export_{args.format}_{ts}"

    if args.split > 0:
        random.seed(args.seed)
        random.shuffle(converted)
        split_idx = max(1, int(len(converted) * args.split))
        val_set = converted[:split_idx]
        train_set = converted[split_idx:]

        train_path = OUTPUTS_DIR / f"{base_name}_train.jsonl"
        val_path = OUTPUTS_DIR / f"{base_name}_val.jsonl"

        if not args.overwrite:
            for p in (train_path, val_path):
                if p.exists():
                    log.error(f"Output already exists: {p}. Use --overwrite.")
                    sys.exit(1)

        write_jsonl(train_set, train_path)
        write_jsonl(val_set, val_path)
        print(f"Train: {len(train_set)} records → {train_path}")
        print(f"Val:   {len(val_set)} records → {val_path}")
    else:
        out_path = OUTPUTS_DIR / f"{base_name}.jsonl"
        if not args.overwrite and out_path.exists():
            log.error(f"Output already exists: {out_path}. Use --overwrite.")
            sys.exit(1)
        write_jsonl(converted, out_path)
        print(f"Exported {len(converted)} records → {out_path}")


if __name__ == "__main__":
    main()

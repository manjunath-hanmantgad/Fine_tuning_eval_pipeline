#!/usr/bin/env python3
"""Run baseline evaluation: send instructions through a Claude model and record responses."""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

OUTPUTS_DIR = Path("outputs")
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def load_eval_records(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if "instruction" not in record:
                    log.warning(f"Line {line_num}: skipping record without 'instruction'")
                    continue
                records.append(record)
            except json.JSONDecodeError:
                log.warning(f"Line {line_num}: skipping invalid JSON")
    return records


def call_model(client, model: str, instruction: str, context: str = "", system: str = "") -> str:
    user_content = f"{instruction}\n\n{context}".strip() if context else instruction
    kwargs: dict = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": user_content}],
    }
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def run_eval(records: list[dict], model: str, max_records: int | None, delay: float) -> list[dict]:
    try:
        import anthropic
    except ImportError:
        log.error("anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    subset = records[:max_records] if max_records else records
    results = []

    for i, record in enumerate(subset, 1):
        log.info(f"Evaluating record {i}/{len(subset)}: {record['instruction'][:60]}...")
        try:
            response_text = call_model(
                client,
                model,
                instruction=record["instruction"],
                context=record.get("input", ""),
                system=record.get("system", ""),
            )
            results.append({
                "instruction": record["instruction"],
                "input": record.get("input", ""),
                "reference": record.get("response", ""),
                "model_response": response_text,
                "model": model,
                "status": "ok",
            })
        except Exception as e:
            log.error(f"Record {i} failed: {e}")
            results.append({
                "instruction": record["instruction"],
                "input": record.get("input", ""),
                "reference": record.get("response", ""),
                "model_response": "",
                "model": model,
                "status": f"error: {e}",
            })

        if delay > 0 and i < len(subset):
            time.sleep(delay)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline evaluation on a JSONL dataset.")
    parser.add_argument("input", type=Path, help="Input JSONL file with instructions")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Claude model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-records", type=int, default=None,
                        help="Limit evaluation to first N records")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay between API calls in seconds (default: 0.5)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output JSONL path (default: outputs/eval_<model>_<timestamp>.jsonl)")
    args = parser.parse_args()

    if not args.input.exists():
        log.error(f"File not found: {args.input}")
        sys.exit(1)

    records = load_eval_records(args.input)
    if not records:
        log.error("No valid records found")
        sys.exit(1)

    log.info(f"Loaded {len(records)} records. Model: {args.model}")
    results = run_eval(records, args.model, args.max_records, args.delay)

    OUTPUTS_DIR.mkdir(exist_ok=True)
    if args.output:
        out_path = args.output
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_model = args.model.replace("/", "-").replace(":", "-")
        out_path = OUTPUTS_DIR / f"eval_{safe_model}_{ts}.jsonl"

    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    ok = sum(1 for r in results if r["status"] == "ok")
    log.info(f"Done. {ok}/{len(results)} succeeded → {out_path}")
    sys.exit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()

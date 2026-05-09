#!/usr/bin/env python3
"""Estimate fine-tuning cost for a JSONL dataset.

Reads a JSONL instruction dataset, counts tokens (using tiktoken if available,
otherwise word-count heuristic), and prints a cost table using publicly known
fine-tuning prices.

Usage:
    python scripts/cost_estimate.py data/sample_instructions.jsonl
    python scripts/cost_estimate.py data/sample_instructions.jsonl --provider openai
    python scripts/cost_estimate.py data/sample_instructions.jsonl --model gpt-4o-mini-2024-07-18
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Fine-tuning prices (USD per 1K tokens) — update when providers change prices.
# Sources:
#   Anthropic: https://docs.anthropic.com/en/docs/about-claude/pricing
#   OpenAI:    https://openai.com/api/pricing/
FINETUNE_PRICES: dict[str, dict[str, dict[str, float]]] = {
    "anthropic": {
        # Training cost per 1K tokens
        "claude-haiku-4-5-20251001":   {"training_per_1k": 0.40,  "inference_per_1k": 0.80},
        "claude-sonnet-4-20250514":    {"training_per_1k": 3.00,  "inference_per_1k": 15.00},
    },
    "openai": {
        "gpt-4o-mini-2024-07-18":      {"training_per_1k": 3.00,  "inference_per_1k": 0.60},
        "gpt-4o-2024-08-06":           {"training_per_1k": 25.00, "inference_per_1k": 3.75},
    },
}

# Default model per provider
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini-2024-07-18",
}


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (exact) or heuristic fallback.

    Mirrors the logic in scripts/diagnostics.py.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return max(1, round(len(text.split()) * 1.3))


def total_tokens(path: Path) -> int:
    """Count tokens across all records in a JSONL dataset."""
    total = 0
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                total += count_tokens(record.get("instruction", ""))
                total += count_tokens(record.get("input", ""))
                total += count_tokens(record.get("response", ""))
            except json.JSONDecodeError:
                log.warning(f"Line {line_num}: skipping invalid JSON — {line[:60]}")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate fine-tuning cost for a JSONL dataset.")
    parser.add_argument("input", type=Path, nargs="?", help="Input JSONL file (Alpaca format)")
    parser.add_argument("--provider", choices=sorted(FINETUNE_PRICES), default="anthropic",
                        help="Fine-tuning provider (default: anthropic)")
    parser.add_argument("--model", type=str, default=None,
                        help=f"Model name (default: provider-specific, see --list-models)")
    parser.add_argument("--list-models", action="store_true",
                        help="List supported models and their prices, then exit")
    args = parser.parse_args()

    if args.list_models:
        print("Supported models and fine-tuning prices:\n")
        for provider in sorted(FINETUNE_PRICES):
            print(f"  {provider}:")
            for model, prices in FINETUNE_PRICES[provider].items():
                print(f"    {model}")
                print(f"      Training:   ${prices['training_per_1k']:.2f} / 1K tokens")
                print(f"      Inference:  ${prices['inference_per_1k']:.2f} / 1K tokens")
        sys.exit(0)

    if args.input is None:
        log.error("Input file required. Use --list-models to see supported models.")
        sys.exit(1)

    if not args.input.exists():
        log.error(f"File not found: {args.input}")
        sys.exit(1)

    model = args.model or DEFAULT_MODELS[args.provider]

    if args.provider not in FINETUNE_PRICES or model not in FINETUNE_PRICES[args.provider]:
        log.error(f"Unknown model '{model}' for provider '{args.provider}'. Use --list-models.")
        sys.exit(1)

    tok = total_tokens(args.input)

    prices = FINETUNE_PRICES[args.provider][model]
    train_cost = tok * prices["training_per_1k"] / 1000
    inf_cost = prices["inference_per_1k"]

    # Determine which token counting method was used
    try:
        import tiktoken  # noqa: F401
        method = "tiktoken (exact)"
    except ImportError:
        method = "heuristic (word_count × 1.3)"

    print(f"\n{'=' * 50}")
    print("  Fine-Tuning Cost Estimate")
    print(f"{'=' * 50}")
    print(f"  Dataset:           {args.input}")
    print(f"  Provider:          {args.provider}")
    print(f"  Model:             {model}")
    print(f"  Token method:      {method}")
    print(f"  Total tokens:      {tok:,}")
    print()
    print(f"  Estimated training cost:     ${train_cost:.2f}")
    print(f"  Estimated inference cost:    ${inf_cost:.2f} / 1K calls")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Training stub — placeholder for Hugging Face PEFT LoRA fine-tuning.

This script is a STRUCTURAL STUB. It does not train any model.

What this script shows:
    - The CLI interface a real training script would use.
    - Where LoRA config, model loading, dataset preparation, and training
      loop would be wired together.
    - The format of exported JSONL files that the training framework expects.

To activate training you would need:
    1. pip install torch transformers datasets peft trl bitsandbytes
    2. A GPU (or Apple Silicon with MPS).
    3. A base model checkpoint (e.g., from Hugging Face Hub).
    4. Implement each # TODO: section below.

Usage:
    python scripts/train_stub.py outputs/export_openai_*.jsonl --dry-run
    python scripts/train_stub.py outputs/export_openai_*.jsonl --model bert-base-uncased --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def validate_export_format(path: Path) -> bool:
    """Check that the exported JSONL has the expected fine-tuning format.

    Currently validates the OpenAI messages[] format:
        {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

    Returns True if all records look valid.
    """
    valid = 0
    errors = 0
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                msgs = record.get("messages", [])
                if len(msgs) < 2:
                    log.warning(f"Line {line_num}: expected at least 2 messages, got {len(msgs)}")
                    errors += 1
                    continue
                roles = [m.get("role", "") for m in msgs]
                if "user" not in roles or "assistant" not in roles:
                    log.warning(f"Line {line_num}: missing user/assistant role in messages")
                    errors += 1
                    continue
                valid += 1
            except json.JSONDecodeError:
                log.warning(f"Line {line_num}: invalid JSON")
                errors += 1

    log.info(f"Validated {path}: {valid} valid, {errors} error(s)")
    return errors == 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Training stub — validate exported JSONL format for fine-tuning compatibility."
    )
    parser.add_argument("input", type=Path, help="Exported JSONL file (OpenAI format)")
    parser.add_argument("--model", type=str, default="bert-base-uncased",
                        help="Base model name (default: bert-base-uncased)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate the exported format without running training")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"),
                        help="Directory for training artifacts (default: outputs/)")
    args = parser.parse_args()

    if not args.input.exists():
        log.error(f"File not found: {args.input}")
        sys.exit(1)

    if args.dry_run:
        ok = validate_export_format(args.input)
        if ok:
            print(f"\nDry-run PASS: {args.input} is compatible with training format.\n")
        else:
            print(f"\nDry-run FAIL: {args.input} has format errors (see warnings above).\n")
        sys.exit(0 if ok else 1)

    print(f"\n{'=' * 60}")
    print("  Training Stub — No training code is implemented.")
    print(f"{'=' * 60}")
    print(f"  Input:     {args.input}")
    print(f"  Model:     {args.model}")
    print(f"  Output:    {args.output_dir}")
    print()
    print("  To activate training, implement the following sections:")
    print()

    sections = [
        ("1. LoRA config",
         "# TODO: from peft import LoraConfig, get_peft_model\n"
         "# lora_config = LoraConfig(\n"
         "#     r=8, lora_alpha=16, target_modules=['q_proj', 'v_proj'],\n"
         "#     lora_dropout=0.05, bias='none', task_type='CAUSAL_LM',\n"
         "# )"),
        ("2. Load base model",
         "# TODO: from transformers import AutoModelForCausalLM, AutoTokenizer\n"
         "# model = AutoModelForCausalLM.from_pretrained(args.model)\n"
         "# tokenizer = AutoTokenizer.from_pretrained(args.model)\n"
         "# model = get_peft_model(model, lora_config)"),
        ("3. Load dataset",
         "# TODO: from datasets import Dataset, load_dataset\n"
         "# raw = [json.loads(line) for line in open(args.input) if line.strip()]\n"
         "# dataset = Dataset.from_list(raw)"),
        ("4. Tokenize",
         "# TODO: def tokenize_fn(batch):\n"
         "#     texts = [m['content'] for m in batch['messages']]\n"
         "#     return tokenizer(texts, truncation=True, padding='max_length', max_length=512)\n"
         "# tokenized = dataset.map(tokenize_fn, batched=True)"),
        ("5. Training arguments",
         "# TODO: from transformers import TrainingArguments\n"
         "# training_args = TrainingArguments(\n"
         "#     output_dir=str(args.output_dir),\n"
         "#     num_train_epochs=3, per_device_train_batch_size=4,\n"
         "#     learning_rate=2e-4, fp16=True,\n"
         "# )"),
        ("6. Trainer",
         "# TODO: from trl import SFTTrainer\n"
         "# trainer = SFTTrainer(\n"
         "#     model=model, args=training_args,\n"
         "#     train_dataset=tokenized,\n"
         "#     tokenizer=tokenizer,\n"
         "# )\n"
         "# trainer.train()"),
        ("7. Save",
         "# TODO: model.save_pretrained(args.output_dir / 'lora-final')\n"
         "# tokenizer.save_pretrained(args.output_dir / 'lora-final')"),
    ]

    for title, code in sections:
        print(f"  {title}")
        for line in code.split("\n"):
            print(f"    {line}")
        print()

    print(f"{'=' * 60}\n")
    print("  Use --dry-run to validate your exported JSONL format first.")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate a JSONL instruction dataset for fine-tuning readiness."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

REQUIRED_FIELDS = {"instruction", "response"}
OPTIONAL_FIELDS = {"input", "system"}

MIN_INSTRUCTION_LEN = 5
MIN_RESPONSE_LEN = 10
MAX_INSTRUCTION_LEN = 2000
MAX_RESPONSE_LEN = 4000


def validate_record(record: dict, line_num: int) -> list[str]:
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Line {line_num}: missing required field '{field}'")
        elif not isinstance(record[field], str):
            errors.append(f"Line {line_num}: field '{field}' must be a string")
        elif not record[field].strip():
            errors.append(f"Line {line_num}: field '{field}' is empty")

    if "instruction" in record and isinstance(record["instruction"], str):
        length = len(record["instruction"])
        if length < MIN_INSTRUCTION_LEN:
            errors.append(f"Line {line_num}: instruction too short ({length} chars, min {MIN_INSTRUCTION_LEN})")
        elif length > MAX_INSTRUCTION_LEN:
            errors.append(f"Line {line_num}: instruction too long ({length} chars, max {MAX_INSTRUCTION_LEN})")

    if "response" in record and isinstance(record["response"], str):
        length = len(record["response"])
        if length < MIN_RESPONSE_LEN:
            errors.append(f"Line {line_num}: response too short ({length} chars, min {MIN_RESPONSE_LEN})")
        elif length > MAX_RESPONSE_LEN:
            errors.append(f"Line {line_num}: response too long ({length} chars, max {MAX_RESPONSE_LEN})")

    unknown = set(record.keys()) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if unknown:
        errors.append(f"Line {line_num}: unexpected fields {unknown}")

    return errors


def validate_file(path: Path) -> dict:
    errors = []
    records = []
    parse_errors = 0

    try:
        fh = open(path, encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError):
        return {
            "total_records": 0,
            "valid_records": 0,
            "parse_errors": 0,
            "validation_errors": [f"Unable to read file: {path}"],
            "duplicate_groups": 0,
            "duplicate_details": [],
            "passed": False,
        }

    try:
        with fh as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append((line_num, record))
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: invalid JSON — {e}")
                    parse_errors += 1
    except UnicodeDecodeError:
        log.warning(f"File is not valid UTF-8: {path}")
        return {
            "total_records": 0,
            "valid_records": 0,
            "parse_errors": 0,
            "validation_errors": [f"File is not valid UTF-8: {path}"],
            "duplicate_groups": 0,
            "duplicate_details": [],
            "passed": False,
        }

    for line_num, record in records:
        errors.extend(validate_record(record, line_num))

    if len(records) == 0:
        errors.append("No valid records found (file empty or only blank/invalid lines)")

    seen: Counter = Counter()
    for _, record in records:
        key = (record.get("instruction", ""), record.get("input", ""))
        seen[key] += 1
    duplicates = [(k, v) for k, v in seen.items() if v > 1]

    return {
        "total_records": len(records) + parse_errors,
        "valid_records": len(records),
        "parse_errors": parse_errors,
        "validation_errors": errors,
        "duplicate_groups": len(duplicates),
        "duplicate_details": duplicates,
        "passed": len(errors) == 0 and len(duplicates) == 0 and len(records) > 0,
    }


def print_report(result: dict, verbose: bool = False) -> None:
    print("\n=== Dataset Validation Report ===")
    print(f"Total records:      {result['total_records']}")
    print(f"Parse errors:       {result['parse_errors']}")
    print(f"Duplicate groups:   {result['duplicate_groups']}")
    print(f"Validation errors:  {len(result['validation_errors'])}")
    print(f"Status:             {'PASS' if result['passed'] else 'FAIL'}")

    if result["validation_errors"]:
        limit = None if verbose else 5
        header = "\nErrors:" if verbose else "\nFirst 5 errors (use --verbose for all):"
        print(header)
        for err in result["validation_errors"][:limit]:
            print(f"  {err}")

    if result["duplicate_details"] and verbose:
        print("\nDuplicates:")
        for (inst, _), count in result["duplicate_details"]:
            print(f"  [{count}x] {inst[:60]}...")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a JSONL instruction dataset.")
    parser.add_argument("input", type=Path, help="Path to input JSONL file")
    parser.add_argument("--verbose", action="store_true", help="Show all errors and duplicates")
    args = parser.parse_args()

    if not args.input.exists():
        log.error(f"File not found: {args.input}")
        sys.exit(1)

    if args.input.is_dir():
        log.error(f"Input is a directory, not a file: {args.input}")
        sys.exit(1)

    result = validate_file(args.input)

    if result["valid_records"] == 0 and not result["validation_errors"]:
        log.error("No valid records found (file empty or only blank lines)")

    print_report(result, verbose=args.verbose)
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()

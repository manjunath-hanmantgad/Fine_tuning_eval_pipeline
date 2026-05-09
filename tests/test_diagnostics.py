import pytest
from pathlib import Path
from scripts.diagnostics import run_diagnostics, estimate_tokens, field_stats, load_records
import json


def make_records(n: int = 5) -> list[dict]:
    return [
        {
            "instruction": f"What is concept number {i} in software engineering?",
            "response": f"Concept {i} refers to an important principle used widely in building robust systems.",
        }
        for i in range(n)
    ]


def test_estimate_tokens_non_empty():
    result = estimate_tokens("hello world foo bar")
    assert result > 0


def test_estimate_tokens_empty_string():
    assert estimate_tokens("") >= 1


def test_field_stats_correct_min_max():
    stats = field_stats([10, 20, 30, 40, 50])
    assert stats["min"] == 10
    assert stats["max"] == 50
    assert stats["mean"] == 30.0
    assert stats["median"] == 30


def test_field_stats_empty_returns_empty_dict():
    assert field_stats([]) == {}


def test_run_diagnostics_basic_counts():
    records = make_records(10)
    result = run_diagnostics(records)
    assert result["total_records"] == 10
    assert result["records_with_input"] == 0
    assert result["records_with_system"] == 0
    assert result["estimated_total_tokens"] > 0
    assert result["flag_count"] == 0


def test_run_diagnostics_flags_very_short_response():
    records = [{"instruction": "What is Python?", "response": "Yes."}]
    result = run_diagnostics(records)
    assert result["flag_count"] > 0


def test_run_diagnostics_flags_very_short_instruction():
    records = [{"instruction": "Hi", "response": "A much longer response that provides useful information."}]
    result = run_diagnostics(records)
    assert result["flag_count"] > 0


def test_run_diagnostics_with_input_field():
    records = [
        {
            "instruction": "Summarize the following.",
            "input": "Some useful context here.",
            "response": "A summary of the context provided above.",
        }
    ]
    result = run_diagnostics(records)
    assert result["records_with_input"] == 1
    assert result["input_length"]


def test_run_diagnostics_instruction_length_stats_present():
    records = make_records(5)
    result = run_diagnostics(records)
    assert "min" in result["instruction_length"]
    assert "max" in result["instruction_length"]
    assert "mean" in result["instruction_length"]


def test_load_records_valid(tmp_path):
    data = [
        {"instruction": "Explain Python.", "response": "Python is a high-level language."},
    ]
    f = tmp_path / "data.jsonl"
    f.write_text(json.dumps(data[0]))
    loaded = load_records(f)
    assert len(loaded) == 1


def test_load_records_skips_invalid_json(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"instruction": "ok", "response": "valid"}\nnot-json\n')
    loaded = load_records(f)
    assert len(loaded) == 1


def test_load_records_blank_file_returns_empty(tmp_path):
    f = tmp_path / "blank.jsonl"
    f.write_text("\n\n\n\n")
    loaded = load_records(f)
    assert loaded == []

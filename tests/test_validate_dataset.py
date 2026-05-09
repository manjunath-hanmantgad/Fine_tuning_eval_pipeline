import json
import pytest
from pathlib import Path
from scripts.validate_dataset import validate_record, validate_file


def test_valid_record():
    record = {"instruction": "What is Python?", "response": "Python is a programming language used widely."}
    assert validate_record(record, 1) == []


def test_missing_response_field():
    errors = validate_record({"instruction": "What is Python?"}, 1)
    assert any("missing required field 'response'" in e for e in errors)


def test_missing_instruction_field():
    errors = validate_record({"response": "A long enough response here."}, 1)
    assert any("missing required field 'instruction'" in e for e in errors)


def test_empty_instruction():
    errors = validate_record({"instruction": "   ", "response": "A valid response here."}, 1)
    assert any("'instruction' is empty" in e for e in errors)


def test_empty_response():
    errors = validate_record({"instruction": "What is Python?", "response": ""}, 1)
    assert any("'response' is empty" in e for e in errors)


def test_instruction_too_short():
    errors = validate_record({"instruction": "Hi", "response": "A valid long enough response."}, 1)
    assert any("instruction too short" in e for e in errors)


def test_response_too_short():
    errors = validate_record({"instruction": "What is Python?", "response": "No"}, 1)
    assert any("response too short" in e for e in errors)


def test_unknown_fields_flagged():
    record = {"instruction": "What is Python?", "response": "A programming language.", "extra": "x"}
    errors = validate_record(record, 1)
    assert any("unexpected fields" in e for e in errors)


def test_optional_fields_allowed():
    record = {
        "instruction": "What is Python?",
        "input": "Explain briefly.",
        "system": "You are a tutor.",
        "response": "Python is a high-level programming language.",
    }
    assert validate_record(record, 1) == []


def test_validate_file_all_clean(tmp_path):
    data = [
        {"instruction": "What is Python?", "response": "A high-level programming language used for many purposes."},
        {"instruction": "Explain recursion.", "response": "Recursion is when a function calls itself to solve a problem."},
    ]
    f = tmp_path / "clean.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in data))
    result = validate_file(f)
    assert result["passed"] is True
    assert result["parse_errors"] == 0
    assert result["duplicate_groups"] == 0


def test_validate_file_parse_error(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"instruction": "Valid?", "response": "Yes valid enough response."}\nnot json\n')
    result = validate_file(f)
    assert result["parse_errors"] == 1
    assert result["passed"] is False


def test_validate_file_detects_duplicates(tmp_path):
    record = {"instruction": "What is Python?", "response": "A high-level programming language."}
    f = tmp_path / "dupes.jsonl"
    f.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n")
    result = validate_file(f)
    assert result["duplicate_groups"] == 1
    assert result["passed"] is False


def test_validate_file_empty_lines_ignored(tmp_path):
    record = {"instruction": "What is Python?", "response": "A programming language used widely."}
    f = tmp_path / "spaced.jsonl"
    f.write_text("\n" + json.dumps(record) + "\n\n")
    result = validate_file(f)
    assert result["total_records"] == 1


def test_validate_file_empty_file_fails(tmp_path):
    f = tmp_path / "empty.jsonl"
    f.write_text("")
    result = validate_file(f)
    assert result["passed"] is False
    assert result["valid_records"] == 0


def test_validate_file_only_blank_lines_fails(tmp_path):
    f = tmp_path / "blank.jsonl"
    f.write_text("\n\n\n\n")
    result = validate_file(f)
    assert result["passed"] is False
    assert result["valid_records"] == 0


def test_validate_file_rejects_directory_input(tmp_path):
    result = validate_file(tmp_path)
    assert result["passed"] is False
    assert any("Unable to read" in e or "not a file" in e or "directory" in e
               for e in result.get("validation_errors", []))


def test_validate_file_rejects_non_utf8(tmp_path):
    import pathlib
    f = tmp_path / "binary.dat"
    f.write_bytes(b"\xff\xfe\x00\x01\x02")
    result = validate_file(f)
    assert result["passed"] is False
    assert any("not valid UTF-8" in e for e in result.get("validation_errors", []))


def test_validate_file_crlf_handling(tmp_path):
    content = '{"instruction": "What is Python?", "response": "A high-level programming language."}\r\n'
    content += '{"instruction": "Explain OOP.", "response": "Object-oriented programming is a paradigm."}\r\n'
    f = tmp_path / "crlf.jsonl"
    f.write_text(content, encoding="utf-8")
    result = validate_file(f)
    assert result["valid_records"] == 2
    assert result["passed"] is True

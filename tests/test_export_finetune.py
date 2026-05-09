import json
import pytest
from pathlib import Path
from scripts.export_finetune import (
    to_openai_format,
    to_anthropic_format,
    to_alpaca_format,
    load_records,
)


def base_record() -> dict:
    return {
        "instruction": "What is Python?",
        "input": "",
        "response": "Python is a high-level programming language.",
    }


def test_openai_format_basic_structure():
    result = to_openai_format(base_record())
    assert "messages" in result
    roles = [m["role"] for m in result["messages"]]
    assert roles == ["user", "assistant"]


def test_openai_format_with_system_prompt():
    record = {**base_record(), "system": "You are a helpful assistant."}
    result = to_openai_format(record)
    roles = [m["role"] for m in result["messages"]]
    assert roles[0] == "system"
    assert len(roles) == 3


def test_openai_format_input_appended_to_user():
    record = {**base_record(), "input": "Context: Python was created by Guido van Rossum."}
    result = to_openai_format(record)
    user_msg = next(m for m in result["messages"] if m["role"] == "user")
    assert "Context:" in user_msg["content"]
    assert "What is Python?" in user_msg["content"]


def test_anthropic_format_basic_structure():
    result = to_anthropic_format(base_record())
    assert "messages" in result
    assert result["messages"][0]["role"] == "user"
    assert result["messages"][1]["role"] == "assistant"
    assert "system" not in result


def test_anthropic_format_with_system():
    record = {**base_record(), "system": "You are a coding tutor."}
    result = to_anthropic_format(record)
    assert result.get("system") == "You are a coding tutor."


def test_alpaca_format_has_required_keys():
    result = to_alpaca_format(base_record())
    assert set(result.keys()) == {"instruction", "input", "response"}


def test_alpaca_format_preserves_values():
    record = base_record()
    result = to_alpaca_format(record)
    assert result["instruction"] == record["instruction"]
    assert result["response"] == record["response"]


def test_load_records_filters_missing_fields(tmp_path, caplog):
    import logging
    records = [
        {"instruction": "Valid?", "response": "Yes valid."},
        {"instruction": "No response field"},
    ]
    f = tmp_path / "data.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in records))
    with caplog.at_level(logging.WARNING):
        loaded = load_records(f)
    assert len(loaded) == 1


def test_load_records_skips_invalid_json(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text('{"instruction": "ok", "response": "valid"}\nnot-json\n')
    loaded = load_records(f)
    assert len(loaded) == 1


def test_load_records_ignores_blank_lines(tmp_path):
    record = {"instruction": "What is Python?", "response": "A programming language."}
    f = tmp_path / "data.jsonl"
    f.write_text("\n" + json.dumps(record) + "\n\n")
    loaded = load_records(f)
    assert len(loaded) == 1


def test_export_overwrite_refuses_without_flag(tmp_path, monkeypatch):
    from scripts.export_finetune import main as export_main
    import sys

    input_file = tmp_path / "input.jsonl"
    input_file.write_text(json.dumps({"instruction": "Test?", "response": "Yes, a test."}) + "\n")

    # First run with --overwrite succeeds
    monkeypatch.setattr(sys, "argv", [
        "export_finetune.py", str(input_file), "--format", "openai", "--overwrite",
    ])
    monkeypatch.chdir(tmp_path)
    export_main()

    # Second run without --overwrite must refuse
    monkeypatch.setattr(sys, "argv", [
        "export_finetune.py", str(input_file), "--format", "openai",
    ])
    with pytest.raises(SystemExit) as exc_info:
        export_main()
    assert exc_info.value.code == 1


def test_export_split_out_of_range_refused(tmp_path, monkeypatch):
    from scripts.export_finetune import main as export_main
    import sys

    input_file = tmp_path / "input.jsonl"
    input_file.write_text(json.dumps({"instruction": "Test?", "response": "Yes, a test."}) + "\n")

    monkeypatch.setattr(sys, "argv", [
        "export_finetune.py", str(input_file), "--format", "openai", "--split", "0.9",
    ])
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        export_main()
    assert exc_info.value.code == 1


def test_export_split_negative_refused(tmp_path, monkeypatch):
    from scripts.export_finetune import main as export_main
    import sys

    input_file = tmp_path / "input.jsonl"
    input_file.write_text(json.dumps({"instruction": "Test?", "response": "Yes, a test."}) + "\n")

    monkeypatch.setattr(sys, "argv", [
        "export_finetune.py", str(input_file), "--format", "openai", "--split", "-0.1",
    ])
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        export_main()
    assert exc_info.value.code == 1

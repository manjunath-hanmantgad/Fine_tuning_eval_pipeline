# Agent Rules — Fine-Tuning & Evaluation Pipeline

## Scope
- Work on one task at a time (see TASKS.md for the ordered list)
- Only modify files relevant to the active task
- Do not begin eval/ work until all scripts/ tasks are complete and tested

## Hard stops — never do these
- Never commit API keys or credentials
- Never delete existing tests to make a test suite pass
- Never invent requirements not listed in TASKS.md or README.md
- Never write to outputs/ — scripts create files there at runtime

## Before marking a task done
- All tests for that component pass: `pytest tests/test_<component>.py -v`
- Script runs end-to-end: `python scripts/<component>.py --help` exits 0
- No hardcoded paths, no debug prints, no secrets left in code

## Escalate (stop and report) when
- Changing data formats that other scripts depend on
- A test fails in a file you did not modify
- Azure / cloud scope appears in a local task
- You are unsure whether a change is in scope — report before acting

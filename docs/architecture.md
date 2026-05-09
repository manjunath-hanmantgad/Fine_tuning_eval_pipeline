# Architecture & Flow Diagrams

---

## 1. End-to-End Pipeline Flow

```mermaid
flowchart LR
    A["📄 Raw Dataset\ndata/sample_instructions.jsonl\n(Alpaca format)"]

    subgraph local ["Local — no API key required"]
        B["validate_dataset.py\nSchema · Length · Duplicates"]
        C["diagnostics.py\nStats · Tokens · Quality flags"]
        D["export_finetune.py\nFormat conversion · Train/val split"]
    end

    subgraph eval ["Eval — requires ANTHROPIC_API_KEY"]
        E["baseline_eval.py\nSend prompts → Claude\nRecord responses"]
        F["compare_report.py\nAlign before/after\nJaccard overlap score"]
    end

    subgraph out ["outputs/ — gitignored"]
        G["diagnostics_*.md"]
        H["export_*.jsonl\n(openai / anthropic / alpaca)"]
        I["eval_*.jsonl"]
        J["compare_*.md"]
    end

    A --> B
    B -->|PASS| C
    B -->|FAIL| K["❌ Fix dataset\nand re-run"]
    C --> G
    C --> D
    D --> H
    H --> E
    E --> I
    I --> F
    F --> J
```

---

## 2. Data Format Transformations

```mermaid
flowchart TD
    IN["Alpaca Input\n───────────────\ninstruction: string\ninput: string (optional)\nresponse: string\nsystem: string (optional)"]

    IN --> EX["export_finetune.py\n--format openai|anthropic|alpaca\n--split 0.0–0.3"]

    EX --> OA["OpenAI Format\n───────────────\n{messages: [\n  {role: system, content: ...},\n  {role: user, content: ...},\n  {role: assistant, content: ...}\n]}"]

    EX --> AN["Anthropic Format\n───────────────\n{system: ...,\n messages: [\n  {role: user, content: ...},\n  {role: assistant, content: ...}\n]}"]

    EX --> AL["Alpaca Passthrough\n───────────────\n{instruction: ...,\n input: ...,\n response: ...}"]

    EX --> SP["Train / Val Split\n───────────────\nexport_*_train.jsonl\nexport_*_val.jsonl\n(seeded shuffle, max 30% val)"]
```

---

## 3. Component & Responsibility Map

```mermaid
graph TB
    subgraph data ["data/"]
        D1["sample_instructions.jsonl\n25 records · Alpaca format"]
    end

    subgraph scripts ["scripts/  (local, zero ML deps)"]
        S1["validate_dataset.py\n· Required fields\n· Length bounds\n· Duplicate detection\n· UTF-8 · CRLF · dir check"]
        S2["diagnostics.py\n· Char/token stats (p50/p90/p99)\n· Quality flags\n· Markdown report"]
        S3["export_finetune.py\n· Format conversion\n· Train/val split\n· Overwrite guard"]
        S4["run_demo.sh\n· Full pipeline in one command\n· No API key needed"]
    end

    subgraph eval ["eval/  (requires ANTHROPIC_API_KEY)"]
        E1["baseline_eval.py\n· Calls Claude API\n· Saves responses as JSONL\n· Per-record error handling"]
        E2["compare_report.py\n· Aligns by instruction text\n· Jaccard word overlap\n· Markdown table output"]
    end

    subgraph tests ["tests/  (43 tests, pytest)"]
        T1["test_validate_dataset.py\n16 tests"]
        T2["test_diagnostics.py\n12 tests"]
        T3["test_export_finetune.py\n15 tests"]
    end

    D1 --> S1 & S2 & S3
    S3 --> E1
    E1 --> E2

    S1 -. tested by .-> T1
    S2 -. tested by .-> T2
    S3 -. tested by .-> T3
```

---

## 4. CI / Quality Gate Pipeline

```mermaid
flowchart LR
    P["Push / PR\nto main"] --> Q

    subgraph Q ["quality-gate (blocks test job)"]
        Q1["No bare except:"]
        Q2["No hardcoded /Users/ paths"]
        Q3["No exposed API keys"]
    end

    Q --> T

    subgraph T ["test (matrix)"]
        T1["Python 3.10"]
        T2["Python 3.11"]
        T3["Python 3.12"]
    end

    T --> S["demo-smoke\nbash scripts/run_demo.sh\nPython 3.12"]

    style Q fill:#fff3cd
    style T fill:#d1ecf1
    style S fill:#d4edda
```

---

## 5. Error Handling & Exit Codes

```mermaid
flowchart TD
    I["Input file path"] --> C1{"File exists?"}
    C1 -->|No| E1["log.error: File not found\nexit 1"]
    C1 -->|Yes| C2{"Is a file\nnot a dir?"}
    C2 -->|No| E2["log.error: Input is a directory\nexit 1"]
    C2 -->|Yes| C3{"Valid UTF-8?"}
    C3 -->|No| E3["log.warning: Not valid UTF-8\nexit 1"]
    C3 -->|Yes| C4{"Records > 0?"}
    C4 -->|No| E4["log.error: No valid records found\nexit 1"]
    C4 -->|Yes| P["Process file\nline by line"]
    P --> C5{"All records\nvalid?"}
    C5 -->|Yes| OK["Print PASS report\nexit 0"]
    C5 -->|No| FAIL["Print FAIL report\nwith error list\nexit 1"]
```

#!/usr/bin/env bash
# Fine-Tuning Evaluation Pipeline — Demo Script
# Runs the full local pipeline end-to-end. No API key required.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_FILE="$PROJECT_DIR/data/sample_instructions.jsonl"

echo "============================================"
echo " Fine-Tuning Evaluation Pipeline Demo"
echo "============================================"
echo ""

# Step 1 — Validate the dataset
echo "--- Step 1: Validate Dataset ---"
python3 "$PROJECT_DIR/scripts/validate_dataset.py" "$DATA_FILE"

echo ""

# Step 2 — Run diagnostics
echo "--- Step 2: Dataset Diagnostics ---"
python3 "$PROJECT_DIR/scripts/diagnostics.py" "$DATA_FILE"

echo ""

# Step 3 — Export to OpenAI format
echo "--- Step 3: Export (OpenAI format) ---"
python3 "$PROJECT_DIR/scripts/export_finetune.py" "$DATA_FILE" --format openai --overwrite

echo ""

# Step 4 — Export to Anthropic format
echo "--- Step 4: Export (Anthropic format) ---"
python3 "$PROJECT_DIR/scripts/export_finetune.py" "$DATA_FILE" --format anthropic --overwrite

echo ""

# Step 5 — Export with train/val split
echo "--- Step 5: Export with Train/Val Split (20%) ---"
python3 "$PROJECT_DIR/scripts/export_finetune.py" "$DATA_FILE" --format openai --split 0.2 --overwrite

echo ""
echo "============================================"
echo " Demo Complete"
echo "============================================"

# Summary
echo ""
echo "Generated files in $PROJECT_DIR/outputs/"

RECORD_COUNT=$(wc -l < "$DATA_FILE" | tr -d ' ')

# Find the latest diagnostics report
DIAG_MD=$(ls -t "$PROJECT_DIR"/outputs/diagnostics_*.md 2>/dev/null | head -1)
TOKEN_ESTIMATE=""
if [ -n "$DIAG_MD" ]; then
    TOKEN_ESTIMATE=$(grep -oE 'Estimated total tokens: [0-9,]+' "$DIAG_MD" | sed 's/Estimated total tokens: //' 2>/dev/null || true)
fi

echo ""
echo "  Input dataset:    $DATA_FILE ($RECORD_COUNT records)"
if [ -n "$TOKEN_ESTIMATE" ]; then
    echo "  Token estimate:   $TOKEN_ESTIMATE"
fi
echo ""
echo "  Outputs:"
for f in "$PROJECT_DIR"/outputs/export_*.jsonl "$PROJECT_DIR"/outputs/diagnostics_*.md; do
    [ -f "$f" ] && echo "    - $(basename "$f")"
done
echo ""
echo "Pipeline finished successfully."

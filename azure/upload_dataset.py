#!/usr/bin/env python3
"""Upload an exported JSONL dataset to Azure Blob Storage.

This is a STUB — the actual upload logic is not implemented.

Credentials:
    AZURE_STORAGE_CONNECTION_STRING — connection string for the storage account
    (read from environment, never from CLI args)

Usage:
    python azure/upload_dataset.py \
        --account myaccount \
        --container mycontainer \
        --file outputs/export_openai_20251001_120000.jsonl

To activate this script:
    pip install azure-storage-blob
    export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=...;AccountName=...;AccountKey=...;"
    Then implement each # TODO: section below.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a dataset JSONL file to Azure Blob Storage.")
    parser.add_argument("--account", required=True, help="Azure Storage account name")
    parser.add_argument("--container", required=True, help="Blob container name")
    parser.add_argument("--file", required=True, type=Path, help="Local path to the JSONL file to upload")
    args = parser.parse_args()

    if not args.file.exists():
        log.error(f"File not found: {args.file}")
        sys.exit(1)

    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        log.error("AZURE_STORAGE_CONNECTION_STRING environment variable is not set")
        sys.exit(1)

    blob_name = args.file.name

    print(f"\n{'=' * 50}")
    print("  Azure Blob Upload Stub")
    print(f"{'=' * 50}")
    print(f"  Account:       {args.account}")
    print(f"  Container:     {args.container}")
    print(f"  Local file:    {args.file}")
    print(f"  Blob name:     {blob_name}")
    print(f"  Connection:    {'[set]' if conn_str else '[missing]'}")
    print()
    print("  TODO: Implement upload using azure-storage-blob:")
    print()
    print("    from azure.storage.blob import BlobServiceClient")
    print("    service = BlobServiceClient.from_connection_string(conn_str)")
    print("    blob_client = service.get_blob_client(container=args.container, blob=blob_name)")
    print("    with open(args.file, 'rb') as data:")
    print("        blob_client.upload_blob(data, overwrite=True)")
    print()
    print("  Install: pip install azure-storage-blob")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()

# Azure Integration Guide

This directory contains stubs for uploading fine-tuning datasets to Azure Blob
Storage and deploying fine-tuned models to Azure ML managed online endpoints.

## Prerequisites

- An **Azure account** with an active subscription
- An **Azure ML workspace** (for training and deployment)
- An **Azure Blob Storage** container (for dataset uploads)
- A **GPU compute cluster** in Azure ML (for fine-tuning)
- An **Azure Key Vault** (for storing connection strings and secrets)

## Required credentials (via environment variables)

| Variable | Used by | Purpose |
|---|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | `upload_dataset.py` | Upload exported JSONL to Blob Storage |
| `AZURE_ML_WORKSPACE` | `deploy_endpoint.py` | Azure ML workspace name |
| `AZURE_ML_RESOURCE_GROUP` | `deploy_endpoint.py` | Resource group containing the workspace |
| `AZURE_ML_SUBSCRIPTION_ID` | `deploy_endpoint.py` | Azure subscription ID |

## How the local pipeline connects

1. Run the local pipeline to produce exported datasets:

```bash
bash scripts/run_demo.sh
```

2. Upload the exported files to Blob Storage:

```bash
python azure/upload_dataset.py \
    --account <storage-account-name> \
    --container <container-name> \
    --file outputs/export_openai_<timestamp>.jsonl
```

3. (Future) Trigger a training job in Azure ML using the uploaded dataset.

4. Deploy the fine-tuned model as a managed online endpoint:

```bash
python azure/deploy_endpoint.py \
    --model-name my-fine-tuned-model \
    --endpoint-name my-endpoint \
    --compute-size Standard_NC6s_v3
```

## Architecture

```
┌──────────────────────┐
│  Local pipeline       │
│  (scripts/run_demo.sh)│
│  outputs/*.jsonl     │
└──────────┬───────────┘
           │ upload_dataset.py
           ▼
┌──────────────────────┐
│  Azure Blob Storage   │
│  (training data)      │
└──────────┬───────────┘
           │ Azure ML training job
           ▼
┌──────────────────────┐
│  Azure ML Workspace   │
│  (fine-tuned model)   │
└──────────┬───────────┘
           │ deploy_endpoint.py
           ▼
┌──────────────────────┐
│  Managed Online       │
│  Endpoint (inference) │
└──────────────────────┘
```

## Notes

- All credential handling reads from environment variables only — never from
  CLI arguments or hardcoded values.
- The Azure SDK packages (`azure-storage-blob`, `azure-ai-ml`) are optional
  dependencies; install them with `pip install azure-storage-blob azure-ai-ml`.
- These scripts are stubs — see the `# TODO:` comments inside each file for
  what SDK calls are needed to activate them.

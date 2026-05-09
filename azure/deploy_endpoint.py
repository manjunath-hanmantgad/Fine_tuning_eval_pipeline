#!/usr/bin/env python3
"""Deploy a fine-tuned model to an Azure ML managed online endpoint.

This is a STUB — the actual deployment logic is not implemented.

Credentials (via environment variables):
    AZURE_ML_SUBSCRIPTION_ID    — Azure subscription ID
    AZURE_ML_RESOURCE_GROUP     — Resource group name
    AZURE_ML_WORKSPACE          — Azure ML workspace name

Usage:
    python azure/deploy_endpoint.py \
        --model-name my-fine-tuned-model \
        --endpoint-name my-endpoint \
        --compute-size Standard_NC6s_v3

To activate this script:
    pip install azure-ai-ml
    export AZURE_ML_SUBSCRIPTION_ID="..."
    export AZURE_ML_RESOURCE_GROUP="..."
    export AZURE_ML_WORKSPACE="..."
    Then implement each # TODO: section below.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy a fine-tuned model to an Azure ML managed online endpoint."
    )
    parser.add_argument("--model-name", required=True, help="Name/ID of the registered model in Azure ML")
    parser.add_argument("--endpoint-name", required=True, help="Name for the managed online endpoint")
    parser.add_argument("--compute-size", default="Standard_NC6s_v3",
                        help="VM size for the endpoint (default: Standard_NC6s_v3)")
    parser.add_argument("--instance-count", type=int, default=1,
                        help="Number of instances (default: 1)")
    args = parser.parse_args()

    # Collect required env vars
    subscription_id = os.environ.get("AZURE_ML_SUBSCRIPTION_ID")
    resource_group = os.environ.get("AZURE_ML_RESOURCE_GROUP")
    workspace = os.environ.get("AZURE_ML_WORKSPACE")

    missing = []
    if not subscription_id:
        missing.append("AZURE_ML_SUBSCRIPTION_ID")
    if not resource_group:
        missing.append("AZURE_ML_RESOURCE_GROUP")
    if not workspace:
        missing.append("AZURE_ML_WORKSPACE")

    if missing:
        log.error(f"Missing required environment variable(s): {', '.join(missing)}")
        sys.exit(1)

    print(f"\n{'=' * 50}")
    print("  Azure ML Endpoint Deployment Stub")
    print(f"{'=' * 50}")
    print(f"  Subscription:  {subscription_id}")
    print(f"  Resource group:{resource_group}")
    print(f"  Workspace:     {workspace}")
    print(f"  Model:         {args.model_name}")
    print(f"  Endpoint:      {args.endpoint_name}")
    print(f"  Compute size:  {args.compute_size}")
    print(f"  Instances:     {args.instance_count}")
    print()
    print("  TODO: Implement deployment using azure-ai-ml:")
    print()
    print("    from azure.ai.ml import MLClient")
    print("    from azure.ai.ml.entities import ManagedOnlineEndpoint, ManagedOnlineDeployment")
    print("    from azure.identity import DefaultAzureCredential")
    print()
    print("    ml_client = MLClient(")
    print("        credential=DefaultAzureCredential(),")
    print("        subscription_id=subscription_id,")
    print("        resource_group_name=resource_group,")
    print("        workspace_name=workspace,")
    print("    )")
    print()
    print("    endpoint = ManagedOnlineEndpoint(name=args.endpoint_name)")
    print("    ml_client.online_endpoints.begin_create_or_update(endpoint)")
    print()
    print("    deployment = ManagedOnlineDeployment(")
    print("        name='default',")
    print("        endpoint_name=args.endpoint_name,")
    print("        model=args.model_name,")
    print("        instance_type=args.compute_size,")
    print("        instance_count=args.instance_count,")
    print("    )")
    print("    ml_client.online_deployments.begin_create_or_update(deployment)")
    print()
    print("  Install: pip install azure-ai-ml")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()

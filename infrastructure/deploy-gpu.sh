#!/bin/bash
# Deploy ATI HR Resume Matcher with GPU Support (Consumption-GPU-NC8as-T4)

set -e

# Configuration
RESOURCE_GROUP="ati-products-pocs"
ACA_NAME="ati-hr-resume-matcher"
ACR_NAME="atiproductpocs"
IMAGE_TAG="${IMAGE_TAG:-latest-gpu}"
ACR_IMAGE="${ACR_NAME}.azurecr.io/ati-hr-resume-matcher:${IMAGE_TAG}"

echo "=========================================="
echo "GPU-Enabled Container App Deployment"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Container App:  $ACA_NAME"
echo "Image:          $ACR_IMAGE"
echo "Workload Profile: Consumption-GPU-NC8as-T4"
echo "Resources:      8 vCPU, 56 GiB"
echo "=========================================="
echo ""

# Step 1: Build and push GPU-enabled image
echo "Step 1: Building and pushing GPU-enabled Docker image..."
docker build --platform linux/amd64 -t ati-hr-resume-matcher:${IMAGE_TAG} .
docker tag ati-hr-resume-matcher:${IMAGE_TAG} ${ACR_IMAGE}

echo "Logging into ACR..."
az acr login --name ${ACR_NAME}

echo "Pushing image to ACR..."
docker push ${ACR_IMAGE}

echo "✓ Image pushed successfully!"
echo ""

# Step 2: Deploy/Update Container App with GPU workload profile
echo "Step 2: Deploying Container App with GPU support..."

az containerapp update \
    --name ${ACA_NAME} \
    --resource-group ${RESOURCE_GROUP} \
    --image ${ACR_IMAGE} \
    --cpu 2.0 \
    --memory 4.0Gi \
    --set-env-vars \
        "OLLAMA_BASE_URL=https://ollama.com/api" \
        "OLLAMA_API_KEY=${OLLAMA_API_KEY}" \
        "OLLAMA_MODEL_NAME=qwen3.5:397b" \
        "STREAMLIT_SERVER_PORT=8501" \
    --min-replicas 1 \
    --max-replicas 1

echo ""
echo "✓ Deployment complete!"
echo ""

# Step 3: Get the URL
echo "Step 3: Retrieving application URL..."
APP_URL=$(az containerapp show \
    --name ${ACA_NAME} \
    --resource-group ${RESOURCE_GROUP} \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo "Application URL: https://${APP_URL}"
echo ""
echo "Using Ollama Cloud API for inference"
echo "Expected Performance:"
echo "  - Startup: 2-5 minutes"
echo "  - Inference: 3-8 seconds per request"
echo "=========================================="

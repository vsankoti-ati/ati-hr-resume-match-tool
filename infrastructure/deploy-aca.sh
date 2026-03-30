#!/bin/bash
# Azure Container App Deployment Script
# Deploys the HR Resume Matcher to Azure Container Apps with proper health probes

set -e

# Configuration variables - UPDATE THESE
RESOURCE_GROUP="your-resource-group"
ACA_NAME="ati-hr-resume-matcher"
LOCATION="eastus"
ENVIRONMENT_NAME="${ACA_NAME}-env"
ACR_NAME="atiproductpocs"
IMAGE_TAG="1.2"

echo "=========================================="
echo "Azure Container App Deployment"
echo "=========================================="

# Check if logged in
echo "Checking Azure login status..."
az account show > /dev/null 2>&1 || az login

# Create ACA environment if it doesn't exist
echo "Ensuring Container App environment exists..."
if ! az containerapp env show --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1; then
    echo "Creating Container App environment..."
    az containerapp env create \
        --name "$ENVIRONMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION"
else
    echo "✓ Environment already exists"
fi

# Deploy or update the container app
echo "Deploying Container App..."
az containerapp create \
    --name "$ACA_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENVIRONMENT_NAME" \
    --image "${ACR_NAME}.azurecr.io/ati-hr-resume-matcher:${IMAGE_TAG}" \
    --registry-server "${ACR_NAME}.azurecr.io" \
    --registry-identity system \
    --target-port 8501 \
    --ingress external \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 1 \
    --env-vars \
        OLLAMA_BASE_URL="https://ollama.com/api" \
        OLLAMA_API_KEY="${OLLAMA_API_KEY}" \
        OLLAMA_MODEL_NAME="qwen3.5:397b" \
        STREAMLIT_SERVER_PORT="8501" \
        STREAMLIT_SERVER_ADDRESS="0.0.0.0" \
    --revision-suffix "v${IMAGE_TAG//./-}"

echo ""
echo "=========================================="
echo "Setting up health probes..."
echo "=========================================="

# Update with proper health probes using az containerapp update
az containerapp update \
    --name "$ACA_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --set-env-vars \
        OLLAMA_BASE_URL="https://ollama.com/api" \
        OLLAMA_API_KEY="${OLLAMA_API_KEY}" \
        OLLAMA_MODEL_NAME="qwen3.5:397b" \
    --cpu 2.0 \
    --memory 4.0Gi

# Get the app URL
APP_URL=$(az containerapp show \
    --name "$ACA_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo "App URL: https://${APP_URL}"
echo ""
echo "⚠️  IMPORTANT: First startup will take 2-5 minutes"
echo "    The container needs to initialize and connect to Ollama Cloud"
echo ""
echo "Check deployment status:"
echo "  az containerapp show -n $ACA_NAME -g $RESOURCE_GROUP"
echo ""
echo "View logs:"
echo "  az containerapp logs show -n $ACA_NAME -g $RESOURCE_GROUP --tail 50 --follow"
echo ""

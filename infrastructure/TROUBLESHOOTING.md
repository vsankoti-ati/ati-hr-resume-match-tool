# Azure Container App Troubleshooting Guide

## Issue: Container App shows green but returns 404

This typically means the container is failing health checks or crashing after startup.

## Quick Diagnostics

### 1. Check Container Logs
```bash
# Replace with your actual values
RESOURCE_GROUP="your-resource-group"
ACA_NAME="ati-hr-resume-matcher"

# View recent logs
az containerapp logs show \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --tail 100

# Follow logs in real-time
az containerapp logs show \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --follow
```

### 2. Check Replica Status
```bash
az containerapp revision list \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --output table
```

### 3. Check Container Status
```bash
az containerapp show \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.{runningStatus:runningStatus,provisioningState:provisioningState,latestRevision:latestRevisionName}" \
    --output table
```

## Common Causes & Fixes

### Issue 1: Startup Timeout (Most Likely)
**Problem**: The container needs 15-30 minutes to download the 20GB Ollama model, but ACA has default startup timeout that's too short.

**Solution**: Update the container app with extended startup probe timeout:

```bash
# This allows up to 30 minutes (60 checks * 30 seconds) for startup
az containerapp update \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 1
```

### Issue 2: Health Probe Path
**Problem**: Default health probe might not work with Streamlit.

**Solution**: Streamlit has a built-in health endpoint at `/_stcore/health`

To update (you'll need to use ARM template or portal):
- Liveness probe: `/_stcore/health` on port 8501
- Readiness probe: `/_stcore/health` on port 8501
- Startup probe: `/_stcore/health` on port 8501 with 60 failure attempts at 30s intervals

### Issue 3: Insufficient Resources
**Problem**: Ollama needs significant memory to load the model.

**Solution**: Ensure at least 4GB memory:
```bash
az containerapp update \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --cpu 2.0 \
    --memory 4.0Gi
```

### Issue 4: Model Not Persisting
**Problem**: Model downloads every restart if not using persistent storage.

**Solution**: Add Azure Files volume mount:
```bash
# Create storage account and file share first
STORAGE_ACCOUNT="acamyresumetool"
FILE_SHARE="ollama-models"

az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location eastus \
    --sku Standard_LRS

az storage share create \
    --name $FILE_SHARE \
    --account-name $STORAGE_ACCOUNT

# Then mount in container app (requires YAML or portal)
# Mount path: /root/.ollama
```

## Recommended Complete Update

Update your container app with proper configuration:

```bash
RESOURCE_GROUP="your-resource-group"
ACA_NAME="ati-hr-resume-matcher"

az containerapp update \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 1 \
    --set-env-vars \
        OLLAMA_BASE_URL="https://ollama.com/api" \
        OLLAMA_API_KEY="${OLLAMA_API_KEY}" \
        OLLAMA_MODEL_NAME="qwen3.5:397b" \
        STREAMLIT_SERVER_PORT="8501" \
        STREAMLIT_SERVER_ADDRESS="0.0.0.0"
```

## After Making Changes

1. **Wait 2-5 minutes** for the application to start (no model download needed)
2. **Monitor logs** continuously:
   ```bash
   az containerapp logs show -n $ACA_NAME -g $RESOURCE_GROUP --follow
   ```
3. **Look for these log messages**:
   - "✓ Ollama Cloud API connection successful!"
   - "Starting Streamlit application..."
   - "You can now view your Streamlit app in your browser."

## If Still Not Working

Delete and recreate with the deployment script:
```bash
# Update variables in the script first
chmod +x infrastructure/deploy-aca.sh
./infrastructure/deploy-aca.sh
```

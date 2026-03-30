#!/bin/bash
# Setup Azure Files volume mount for Container App
# Persists Ollama models across container restarts

set -e

# Configuration
RESOURCE_GROUP="ati-products-pocs"
LOCATION="westus2"
STORAGE_ACCOUNT_NAME="atihrresumetoolstorage"  # Change if needed (must be globally unique)
FILE_SHARE_NAME="ollama-models"
ACA_NAME="ati-hr-resume-matcher"
ENVIRONMENT_NAME="ati-hr-resume-matcher-env"  # Update with your actual environment name
IMAGE="atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.8"

echo "=========================================="
echo "Azure Container App Volume Mount Setup"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "File Share: $FILE_SHARE_NAME"
echo "Container App: $ACA_NAME"
echo ""

# Step 1: Create storage account
echo "Step 1: Creating storage account..."
if az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "✓ Storage account already exists"
else
    az storage account create \
        --name $STORAGE_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2
    echo "✓ Storage account created"
fi

# Step 2: Get storage key
echo ""
echo "Step 2: Getting storage account key..."
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].value" \
    --output tsv)
echo "✓ Storage key retrieved"

# Step 3: Create file share
echo ""
echo "Step 3: Creating file share..."
if az storage share show --name $FILE_SHARE_NAME --account-name $STORAGE_ACCOUNT_NAME --account-key $STORAGE_KEY &> /dev/null; then
    echo "✓ File share already exists"
else
    az storage share create \
        --name $FILE_SHARE_NAME \
        --account-name $STORAGE_ACCOUNT_NAME \
        --account-key $STORAGE_KEY \
        --quota 50
    echo "✓ File share created (50 GB)"
fi

# Step 4: Add storage to Container App environment
echo ""
echo "Step 4: Adding storage to Container App environment..."
az containerapp env storage set \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --storage-name ollama-storage \
    --azure-file-account-name $STORAGE_ACCOUNT_NAME \
    --azure-file-account-key $STORAGE_KEY \
    --azure-file-share-name $FILE_SHARE_NAME \
    --access-mode ReadWrite
echo "✓ Storage added to environment"

# Step 5: Verify storage
echo ""
echo "Step 5: Verifying storage configuration..."
az containerapp env storage list \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --output table

# Step 6: Get current environment variables
echo ""
echo "Step 6: Retrieving current container app configuration..."
CURRENT_ENV=$(az containerapp show \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.template.containers[0].env" \
    --output json)

echo "✓ Configuration retrieved"

# Step 7: Update container app with volume mount
echo ""
echo "Step 7: Updating container app with volume mount..."
echo "⚠️  This will create a new revision and restart the container"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 1
fi

# Create temporary YAML file
cat > /tmp/containerapp-update.yaml <<EOF
properties:
  template:
    containers:
    - name: ati-hr-resume-matcher
      image: $IMAGE
      resources:
        cpu: 8.0
        memory: 56Gi
      env:
      - name: OLLAMA_MODEL_NAME
        value: "qwen3.5:397b"
      - name: OLLAMA_BASE_URL
        value: "http://localhost:11434"
      - name: OLLAMA_HOST
        value: "0.0.0.0:11434"
      - name: OLLAMA_TIMEOUT
        value: "1200"
      - name: AZURE_AD_REDIRECT_URI
        value: "https://ati-hr-resume-matcher.icysea-96f1bb84.westus2.azurecontainerapps.io"
      - name: AZURE_AD_TENANT_ID
        value: "7b86ac70-4bbf-4cca-bed2-350e38bf41bd"
      - name: AZURE_AD_CLIENT_ID
        value: "359eccc0-1670-4210-9bc7-195680c8921d"
      - name: AZURE_AD_CLIENT_SECRET
        value: "XXXXXXXX"
      - name: ENABLE_AUTH
        value: "true"
      volumeMounts:
      - volumeName: ollama-volume
        mountPath: /root/.ollama
    volumes:
    - name: ollama-volume
      storageType: AzureFile
      storageName: ollama-storage
    scale:
      minReplicas: 1
      maxReplicas: 1
EOF

az containerapp update \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --yaml /tmp/containerapp-update.yaml

echo "✓ Container app updated with volume mount"

# Clean up
rm /tmp/containerapp-update.yaml

# Step 8: Wait for revision to be ready
echo ""
echo "Step 8: Waiting for new revision to be ready..."
echo "This may take 2-5 minutes..."
sleep 10

MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    RUNNING=$(az containerapp revision list \
        --name $ACA_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "[?properties.active==\`true\`].properties.runningState" \
        --output tsv)
    
    if [ "$RUNNING" == "Running" ]; then
        echo "✓ New revision is running"
        break
    fi
    
    echo "  Waiting... ($ELAPSED seconds)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

# Step 9: Verify volume mount
echo ""
echo "Step 9: Verifying volume mount..."
az containerapp show \
    --name $ACA_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.template.{volumeMounts:containers[0].volumeMounts, volumes:volumes}" \
    --output json

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Monitor logs to see if model is reused:"
echo "   az containerapp logs show -n $ACA_NAME -g $RESOURCE_GROUP --follow"
echo ""
echo "2. Look for: '✓ Model qwen3.5:397b already exists'"
echo ""
echo "3. Access the file share in Azure Portal to verify model files:"
echo "   Storage Account: $STORAGE_ACCOUNT_NAME"
echo "   File Share: $FILE_SHARE_NAME"
echo ""

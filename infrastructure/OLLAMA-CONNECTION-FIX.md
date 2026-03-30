# Streamlit-Ollama Connection Issues Troubleshooting

## Problem
Streamlit application cannot connect to Ollama service running in the same container.

## Changes Made to Fix

### 1. Fixed Ollama Host Binding
**File**: [scripts/entrypoint.sh](../scripts/entrypoint.sh)

Added explicit `OLLAMA_HOST` export before starting Ollama:
```bash
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &
```

This ensures Ollama binds to all interfaces, not just localhost.

### 2. Added Model Warm-up Test
After model is pulled, a test inference request is sent to:
- Load the model into GPU/memory
- Verify the model actually works before Streamlit starts
- Catch connection issues early

### 3. Added Diagnostic Script
**File**: [scripts/diagnose-ollama.sh](../scripts/diagnose-ollama.sh)

Run inside the container to troubleshoot:
```bash
/resume-match-tool/diagnose-ollama.sh
```

## Rebuild and Deploy

```bash
# Rebuild with fixes
docker build --platform linux/amd64 -t ati-hr-resume-matcher .
docker tag ati-hr-resume-matcher atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4-gpu
docker push atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4-gpu

# Update container app
az containerapp update \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --image atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4-gpu
```

## Verify After Deployment

### Check startup logs:
```bash
az containerapp logs show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --tail 100
```

Look for these key messages:
- `✓ Ollama service is ready!`
- `Ollama is listening on: 0.0.0.0:11434`
- `✓ Model inference test successful!`
- `Status: Ready ✓`

### Run diagnostics (if still having issues):
```bash
# Exec into the container
az containerapp exec \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --command /bin/bash

# Run the diagnostic script
/resume-match-tool/diagnose-ollama.sh
```

## Common Issues and Solutions

### Issue 1: "Connection refused" from Streamlit
**Cause**: Ollama not binding to 0.0.0.0
**Solution**: Verify `OLLAMA_HOST=0.0.0.0:11434` is set before `ollama serve`

### Issue 2: "Request timeout" even though Ollama started
**Cause**: Model not loaded into GPU memory yet
**Solution**: The warm-up test now pre-loads the model before Streamlit starts

### Issue 3: Works in startup but fails during runtime
**Cause**: GPU memory exhausted or model unloaded
**Solution**: 
```bash
# Check GPU memory
az containerapp exec --name ati-hr-resume-matcher --resource-group ati-products-pocs --command nvidia-smi

# Verify model is still loaded
az containerapp exec --name ati-hr-resume-matcher --resource-group ati-products-pocs --command "ollama list"
```

### Issue 4: "No response from Ollama"
**Cause**: Ollama process crashed or stopped
**Solution**: Check logs and restart:
```bash
# Check if process running
az containerapp exec --name ati-hr-resume-matcher --resource-group ati-products-pocs --command "pgrep -x ollama"

# If not running, restart the container
az containerapp revision restart \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs
```

## Environment Variables to Verify

In Azure Portal under Container App > Environment variables:

| Variable | Expected Value | Purpose |
|----------|---------------|---------|
| `OLLAMA_HOST` | `0.0.0.0:11434` | Bind to all interfaces |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Streamlit connects here |
| `OLLAMA_MODEL_NAME` | `qwen3.5:397b` | Model to use |
| `OLLAMA_TIMEOUT` | `600` or higher | Request timeout seconds |

## Testing Connection Manually

From within the container:

```bash
# Test API connectivity
curl http://localhost:11434/api/tags

# Test model inference
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3.5:397b",
  "prompt": "Hello",
  "stream": false
}'
```

Both should return JSON responses without errors.

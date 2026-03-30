# Azure Container Apps Debugging Guide

## Running Ollama Diagnostics on ACA

### Method 1: View Startup Diagnostics (Automatic)

The diagnostic script now runs automatically on container startup. View the logs to see the results:

```bash
az containerapp logs show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --tail 200 --follow
```

Look for the section:
```
==========================================
Running Ollama Diagnostics...
==========================================
```

This will show:
- Ollama process status
- Environment variables
- API connectivity tests on localhost, 127.0.0.1, and 0.0.0.0
- Available models
- Inference test results
- Network port bindings
- GPU status (if available)

---

### Method 2: Manually Run Diagnostics (Interactive)

Exec into the running container and run the diagnostic script:

```bash
# Open shell in the container
az containerapp exec \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --command /bin/bash

# Inside the container, run diagnostics
/resume-match-tool/diagnose-ollama.sh
```

---

### Method 3: Quick Manual Checks

If the diagnostic script isn't working, run these commands inside the container:

```bash
# Check if Ollama process is running
pgrep -x ollama

# Check environment variables
env | grep OLLAMA

# Test API connectivity
curl http://localhost:11434/api/tags
curl http://127.0.0.1:11434/api/tags

# Test Ollama Cloud API
curl -H "Authorization: Bearer ${OLLAMA_API_KEY}" https://ollama.com/api/version

# Test inference
curl -X POST https://ollama.com/api/generate \
  -H "Authorization: Bearer ${OLLAMA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:397b",
    "prompt": "Hello",
    "stream": false
  }'
```

---

## Common ACA-Specific Issues

### Issue 1: Ollama Not Binding to Correct Interface

**Symptom**: Logs show "connection refused" or "no route to host"

**Check**:
```bash
# View startup logs
az containerapp logs show -n ati-hr-resume-matcher -g ati-products-pocs --tail 100 | grep "OLLAMA_HOST"
```

**Expected**: `OLLAMA_HOST: 0.0.0.0:11434`

**Fix**: Verify environment variable is set:
```bash
az containerapp show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --query "properties.template.containers[0].env[?name=='OLLAMA_HOST']"
```

---

### Issue 2: Streamlit Using Wrong URL

**Symptom**: Streamlit can't connect to Ollama even though Ollama is running

**Check**:
```bash
az containerapp show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --query "properties.template.containers[0].env[?name=='OLLAMA_BASE_URL']"
```

**Expected**: `http://localhost:11434` or `http://127.0.0.1:11434`

**Fix**: Update environment variable:
```bash
az containerapp update \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --set-env-vars OLLAMA_BASE_URL="http://localhost:11434"
```

---

### Issue 3: Timeout Before Model Loads

**Symptom**: First request times out after 600 seconds

**Solution**: Model needs time to load into memory (especially on CPU)

**Fix**: Increase timeout:
```bash
az containerapp update \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --set-env-vars OLLAMA_TIMEOUT="1200"
```

Or use a smaller model:
```bash
az containerapp update \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --set-env-vars OLLAMA_MODEL_NAME="llama3.2:3b"
```

---

### Issue 4: Container Restarts During Model Download

**Symptom**: Container restarts/fails during initial model download

**Check startup probe settings**:
```bash
az containerapp show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --query "properties.template.containers[0].probes"
```

**Fix**: Extend startup probe timeout (allows 30 minutes for model download):
```bash
# Via Azure Portal:
# Container Apps → ati-hr-resume-matcher → Revision management → Edit and deploy
# → Health probes → Startup probe
# - Initial delay: 30 seconds
# - Period: 30 seconds
# - Failure threshold: 60 (allows 30 minutes total)
```

---

## Complete Diagnostic Workflow

### Step 1: Check if container is running
```bash
az containerapp revision list \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --query "[].{name:name, active:properties.active, replicas:properties.replicas}" \
    --output table
```

### Step 2: View recent logs with automatic diagnostics
```bash
az containerapp logs show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --tail 200
```

### Step 3: Look for key indicators

**Ollama Started Successfully:**
```
✓ Ollama service is ready!
Ollama is listening on: 0.0.0.0:11434
```

**Model Available:**
```
✓ Ollama Cloud API accessible
✓ Model qwen3.5:397b available via cloud
```

**Diagnostic Results:**
```
1. Checking Ollama Cloud API...
   ✓ Ollama Cloud API is accessible

3. Testing API authentication...
   ✓ Bearer token authentication successful

6. Testing model inference...
   ✓ Inference test successful!
```

**Streamlit Started:**
```
Starting Streamlit application...
You can now view your Streamlit app in your browser
```

### Step 4: If diagnostics show failures

Exec into container and run detailed checks:
```bash
az containerapp exec \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --command bash

# Inside container:
/resume-match-tool/diagnose-ollama.sh
```

---

## Debug Connection in Real-Time

### Monitor logs continuously while testing the app:

```bash
# Terminal 1: Monitor logs
az containerapp logs show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --follow

# Terminal 2: Access the app in browser
# Try to run a resume match and watch the logs
```

### Look for these error patterns:

**Connection Refused:**
```
ERROR:utils.ollama_client:Error during generation: Connection refused
```
→ Ollama not running or not binding correctly

**Timeout:**
```
ERROR:utils.ollama_client:Request timed out after 600 seconds
```
→ Model loading too slowly (CPU bottleneck) or not responding

**404 Error:**
```
ERROR:utils.ollama_client:Generation failed: 404
```
→ Model not loaded or API endpoint issue

---

## Rebuild and Redeploy with Diagnostics

If you made changes to fix issues:

```bash
# 1. Rebuild with latest entrypoint script
docker build --platform linux/amd64 -t ati-hr-resume-matcher .
docker tag ati-hr-resume-matcher atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4
docker push atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4

# 2. Update ACA to use new image
az containerapp update \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --image atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4

# 3. Wait 2-3 minutes for new revision to start

# 4. Watch the diagnostic output
az containerapp logs show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --follow
```

---

## Expected Startup Timeline on ACA

| Stage | Duration | What's Happening |
|-------|----------|------------------|
| Container start | 10-30s | Pulling image, starting container |
| API connectivity check | 2-5s | Testing Ollama Cloud API connection |
| Authentication check | 1-2s | Validating API key |
| Diagnostics | 10-20s | Running connectivity and inference tests |
| Streamlit startup | 10-20s | Starting web server |
| **Total** | **~35-80s** | No model download needed |

Since models are hosted in Ollama Cloud, startup is much faster with no model downloads required.

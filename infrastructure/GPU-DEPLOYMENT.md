# GPU-Enabled Deployment for Azure Container Apps

## Changes Made to Enable GPU Support

1. **Dockerfile**: Changed base image from `python:3.11-slim` to `nvidia/cuda:12.4.0-runtime-ubuntu22.04`
2. **Environment Variables**: Added `NVIDIA_VISIBLE_DEVICES=all` and `NVIDIA_DRIVER_CAPABILITIES=compute,utility`
3. **Entrypoint Script**: Added GPU detection to confirm GPU is available

## Build and Deploy GPU-Enabled Image

```bash
# Build with GPU support
docker build --platform linux/amd64 -t ati-hr-resume-matcher .

# Tag for ACR
docker tag ati-hr-resume-matcher atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4-gpu

# Push to ACR
docker push atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4-gpu
```

## Update Container App with GPU Image

```bash
az containerapp update \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --image atiproductpocs.azurecr.io/ati-hr-resume-matcher:1.4-gpu \
    --cpu 8.0 \
    --memory 56Gi
```

## Verify GPU is Being Used

After deployment, check the logs:

```bash
az containerapp logs show \
    --name ati-hr-resume-matcher \
    --resource-group ati-products-pocs \
    --tail 100 | grep -A 2 "GPU"
```

You should see:
```
✓ NVIDIA GPU detected:
Tesla T4, 15360 MiB
```

If you see "⚠️ No GPU detected", the GPU isn't being passed to the container properly.

## Expected Performance with GPU

- **Model load time**: 5-10 seconds (vs 2-5 minutes on CPU)
- **Inference time**: 2-5 seconds per request (vs 600+ seconds on CPU)
- **First request**: ~10 seconds (loads model into GPU memory)
- **Subsequent requests**: 2-5 seconds

## Troubleshooting

### GPU Not Detected

If GPU isn't detected after deployment:

1. **Verify ACA has GPU workload profile**:
   ```bash
   az containerapp show \
       --name ati-hr-resume-matcher \
       --resource-group ati-products-pocs \
       --query "properties.workloadProfileName"
   ```
   Should return a GPU-enabled profile.

2. **Check if the environment supports GPU**:
   ```bash
   az containerapp env show \
       --name <your-env-name> \
       --resource-group ati-products-pocs \
       --query "properties.workloadProfiles"
   ```

3. **Ensure GPU workload profile is used**:
   ```bash
   az containerapp update \
       --name ati-hr-resume-matcher \
       --resource-group ati-products-pocs \
       --workload-profile-name <GPU_PROFILE_NAME>
   ```

### Still Timing Out

If still timing out even with GPU:

1. **Check Ollama logs for GPU usage**:
   ```bash
   az containerapp logs show \
       --name ati-hr-resume-matcher \
       --resource-group ati-products-pocs \
       --follow
   ```
   Look for messages like "using GPU" or "CUDA initialized"

2. **Test Ollama directly**:
   ```bash
   # Exec into container
   az containerapp exec \
       --name ati-hr-resume-matcher \
       --resource-group ati-products-pocs \
       --command /bin/bash
   
   # Inside container
   ollama run qwen3:8b "Hello"
   ```

3. **Monitor GPU usage**:
   If you can exec in:
   ```bash
   watch -n 1 nvidia-smi
   ```
   During inference, GPU utilization should be 80-100%.

## Cost Impact

With GPU-enabled Container App:
- **Estimated cost**: $300-500/month (depending on GPU type and usage)
- **Without GPU**: $50-100/month (but very slow performance)

GPU is essential for acceptable performance with 8B parameter models.

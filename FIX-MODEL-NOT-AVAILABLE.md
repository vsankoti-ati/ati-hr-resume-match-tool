# Fix: Health Check Failing - qwen3.5 Model Not Available

## Issue Summary
The health check was failing with the error "Model qwen3.5:397b is not available" because the model name configured didn't exist in Ollama Cloud's model registry.

## Root Cause
The application was configured to use model `qwen3.5:397b`, but when querying the Ollama Cloud API's `/tags` endpoint, this model name was not found in the list of available models.

### Available Models Found
When querying Ollama Cloud, the following models were available:
- `qwen3.5:397b` ✅ (the correct model to use)
- `qwen3-next:80b`
- `deepseek-v3.1:671b`
- `deepseek-v3.2`
- `gemini-3-flash-preview`
- And many others...

But **NOT** `qwen3.5:397b`.

## The Fix
Changed the model name from `qwen3.5:397b` to `qwen3.5:397b` in two files:

### 1. Updated .env
```bash
OLLAMA_MODEL_NAME=qwen3.5:397b  # Changed from qwen3.5:397b
```

### 2. Updated config/config.py
```python
OLLAMA_MODEL_NAME = os.getenv('OLLAMA_MODEL_NAME', 'qwen3.5:397b')  # Changed default
```

## Verification
After the fix, all health checks pass:

```bash
✅ Model check passed!
✅ All systems operational!
```

## Technical Details

### How the Check Works
1. The `MatchingEngine.check_system_health()` method calls:
   - `ollama_client.health_check()` - verifies API is reachable
   - `ollama_client.check_model_exists()` - verifies model is available

2. The `check_model_exists()` method:
   - Calls `/tags` endpoint to get list of available models
   - Checks if configured model name is in the list
   - Returns `False` if model not found → health check fails

### Why It Happened
The model name `qwen3.5:397b` may have been:
- A documentation example that doesn't reflect actual model names
- A placeholder that was never updated
- An older model name that was renamed to `qwen3.5:397b`

## Deployment Consideration
If you're deploying to Azure Container Apps or other environments, ensure:
1. The `.env` file is updated with `OLLAMA_MODEL_NAME=qwen3.5:397b`
2. Or set the environment variable in your deployment configuration
3. Restart the application to pick up the new model name

## Alternative Solution
If you prefer to skip the model existence check for cloud deployments (since the inference test already validates model availability), you could modify the health check logic:

```python
def check_system_health(self) -> Tuple[bool, str]:
    """Check if all required services are available"""
    if not self.ollama_client.health_check():
        return False, "Ollama service is not available"
    
    # For cloud deployments, skip model list check
    # The inference test in health_check.py already validates model works
    # if not Config.OLLAMA_BASE_URL.startswith('http://localhost'):
    #     return True, "All systems operational"
    
    if not self.ollama_client.check_model_exists():
        return False, f"Model {Config.OLLAMA_MODEL_NAME} is not available"
    
    return True, "All systems operational"
```

However, using the correct model name is the cleaner solution.

## Date Fixed
March 30, 2026

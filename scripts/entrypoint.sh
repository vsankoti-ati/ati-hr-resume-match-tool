#!/bin/bash
# Entrypoint script for combined Ollama + Python App container
# Starts Ollama service in background and Streamlit in foreground

set -e

echo "=========================================="
echo "Starting HR Resume Match Tool Container"
echo "=========================================="

# Check GPU availability
echo "Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "  (GPU info unavailable)"
else
    echo "⚠️  No GPU detected - running on CPU (performance will be slower)"
fi
echo ""

# Start Ollama service in the background
echo "Starting Ollama service..."
# Ensure OLLAMA_HOST is set for binding to all interfaces
# Format: host:port (NOT http://host:port)
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama service to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "✗ Ollama service failed to start within timeout"
        kill $OLLAMA_PID 2>/dev/null || true
        exit 1
    fi
    echo "Ollama not ready yet, waiting... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✓ Ollama service is ready!"
echo "  Ollama is listening on: $OLLAMA_HOST"

# Check if the model exists
echo "Checking if model ${OLLAMA_MODEL_NAME} exists..."
if ollama list 2>/dev/null | grep -q "${OLLAMA_MODEL_NAME}"; then
    echo "✓ Model ${OLLAMA_MODEL_NAME} already exists"
else
    echo "Model not found, pulling ${OLLAMA_MODEL_NAME}..."
    echo "⚠️  This will download ~20GB and may take 15-30 minutes on first run"
    
    ollama pull "${OLLAMA_MODEL_NAME}"
    
    if [ $? -eq 0 ]; then
        echo "✓ Model ${OLLAMA_MODEL_NAME} downloaded successfully!"
    else
        echo "✗ Failed to download model"
        kill $OLLAMA_PID 2>/dev/null || true
        exit 1
    fi
fi

# Show available models
echo "Available models:"
ollama list

echo "=========================================="
echo "Testing Ollama Model Inference..."
echo "=========================================="
echo "Waiting for Ollama runner to fully initialize..."
sleep 5

# Test inference and warm up the model
echo "Sending test prompt to warm up model..."
TEST_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" --max-time 120 http://localhost:11434/api/generate -d '{
  "model": "'"${OLLAMA_MODEL_NAME}"'",
  "prompt": "Say hello in one word.",
  "stream": false,
  "options": {
    "num_predict": 5
  }
}' 2>&1)

HTTP_STATUS=$(echo "$TEST_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE_BODY=$(echo "$TEST_RESPONSE" | sed '/HTTP_STATUS/d')

echo "HTTP Status: ${HTTP_STATUS:-unknown}"

if [ "$HTTP_STATUS" = "200" ] && echo "$RESPONSE_BODY" | grep -q '"response"'; then
    echo "✓ Model inference test successful!"
    echo "  Ollama is ready to handle requests"
    echo "  Response preview: $(echo "$RESPONSE_BODY" | jq -r '.response' 2>/dev/null | head -c 50)..."
elif [ "$HTTP_STATUS" = "500" ]; then
    echo "✗ Model inference FAILED with 500 error!"
    echo "  This usually means:"
    echo "    1. Model failed to load into GPU memory"
    echo "    2. Insufficient GPU VRAM"
    echo "    3. Model name mismatch"
    echo ""
    echo "  Error response: $RESPONSE_BODY"
    echo ""
    echo "  Checking GPU memory..."
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=memory.used,memory.total --format=csv
    fi
    echo ""
    echo "  Available models in Ollama:"
    ollama list
    echo ""
    echo "⚠️  Continuing anyway - Streamlit health checks will catch this"
else
    echo "⚠️  Model inference test had issues (Status: $HTTP_STATUS)"
    echo "  This might be normal on first startup - model will load on first actual request"
    echo "  Response: $RESPONSE_BODY"
fi
echo ""

echo "=========================================="
echo "Running Ollama Diagnostics..."
echo "=========================================="

# Run diagnostic script if it exists
if [ -f "/resume-match-tool/diagnose-ollama.sh" ]; then
    bash /resume-match-tool/diagnose-ollama.sh
else
    echo "⚠️  Diagnostic script not found, running basic checks..."
    
    # Basic diagnostics
    echo "Ollama process: $(ps aux | grep -v grep | grep -q 'ollama serve' && echo '✓ Running' || echo '✗ Not running')"
    echo "Environment:"
    echo "  OLLAMA_HOST: ${OLLAMA_HOST}"
    echo "  OLLAMA_BASE_URL: ${OLLAMA_BASE_URL}"
    
    echo "Testing localhost:11434..."
    curl -sf http://localhost:11434/api/tags > /dev/null && echo "  ✓ Success" || echo "  ✗ Failed"
    
    echo "Testing 127.0.0.1:11434..."
    curl -sf http://127.0.0.1:11434/api/tags > /dev/null && echo "  ✓ Success" || echo "  ✗ Failed"
fi

echo "=========================================="
echo "Connection Test Summary"
echo "=========================================="
echo "  Ollama Host: $OLLAMA_HOST"
echo "  Ollama Base URL: http://localhost:11434"
echo "  Model: $OLLAMA_MODEL_NAME"
echo "  Status: Ready ✓"
echo ""

echo "=========================================="
echo "Starting Streamlit application..."
echo "=========================================="
echo "Access the application at: http://localhost:8501"
echo ""

# Start Streamlit in foreground (this replaces the shell process)
exec streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0

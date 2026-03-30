#!/bin/bash
# Ollama Connection Diagnostic Script
# Use this to troubleshoot connection issues between Streamlit and Ollama

echo "========================================"
echo "Ollama Connection Diagnostics"
echo "========================================"
echo ""

# Check if Ollama process is running
echo "1. Checking Ollama process..."
if ps aux | grep -v grep | grep -q "ollama serve"; then
    echo "   ✓ Ollama process is running (PID: $(ps aux | grep -v grep | grep 'ollama serve' | awk '{print $2}' | head -1))"
else
    echo "   ✗ Ollama process NOT running"
    exit 1
fi
echo ""

# Check environment variables
echo "2. Environment Variables:"
echo "   OLLAMA_HOST: ${OLLAMA_HOST:-not set}"
echo "   OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-not set}"
echo "   OLLAMA_MODEL_NAME: ${OLLAMA_MODEL_NAME:-not set}"
echo ""

# Check if Ollama API is responding
echo "3. Testing Ollama API connectivity..."
echo "   Testing: http://localhost:11434/api/tags"
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✓ Ollama API is responding on localhost:11434"
else
    echo "   ✗ Ollama API not responding on localhost:11434"
fi

echo "   Testing: http://127.0.0.1:11434/api/tags"
if curl -sf http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "   ✓ Ollama API is responding on 127.0.0.1:11434"
else
    echo "   ✗ Ollama API not responding on 127.0.0.1:11434"
fi

echo "   Testing: http://0.0.0.0:11434/api/tags"
if curl -sf http://0.0.0.0:11434/api/tags > /dev/null 2>&1; then
    echo "   ✓ Ollama API is responding on 0.0.0.0:11434"
else
    echo "   ✗ Ollama API not responding on 0.0.0.0:11434"
fi
echo ""

# List available models
echo "4. Available models:"
ollama list
echo ""

# Check if target model is loaded
echo "5. Checking for model: ${OLLAMA_MODEL_NAME}"
if ollama list | grep -q "${OLLAMA_MODEL_NAME}"; then
    echo "   ✓ Model ${OLLAMA_MODEL_NAME} is available"
else
    echo "   ✗ Model ${OLLAMA_MODEL_NAME} NOT found"
fi
echo ""

# Test inference
echo "6. Testing model inference..."
echo "   Sending test prompt to ${OLLAMA_MODEL_NAME}..."
RESPONSE=$(curl -s --max-time 30 http://localhost:11434/api/generate -d '{
  "model": "'"${OLLAMA_MODEL_NAME}"'",
  "prompt": "Say hello",
  "stream": false,
  "options": {
    "num_predict": 10
  }
}')

if echo "$RESPONSE" | grep -q '"response"'; then
    echo "   ✓ Inference test successful!"
    echo "   Response: $(echo $RESPONSE | python3 -c 'import sys, json; print(json.load(sys.stdin).get("response", ""))' 2>/dev/null || echo 'parsing failed')"
else
    echo "   ✗ Inference test failed"
    echo "   Response: $RESPONSE"
fi
echo ""

# Check listening ports
echo "7. Network listening status:"
if command -v netstat &> /dev/null; then
    echo "   Ports listening on 11434:"
    netstat -tuln 2>/dev/null | grep 11434 || echo "   (netstat: no results)"
elif command -v ss &> /dev/null; then
    echo "   Ports listening on 11434:"
    ss -tuln 2>/dev/null | grep 11434 || echo "   (ss: no results)"
else
    echo "   (netstat/ss not available)"
fi
echo ""

# Check GPU
echo "8. GPU Status:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "   nvidia-smi failed"
else
    echo "   No GPU detected"
fi
echo ""

echo "========================================"
echo "Diagnostics Complete"
echo "========================================"

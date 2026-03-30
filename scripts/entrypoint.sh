#!/bin/bash
# Entrypoint script for HR Resume Match Tool
# Starts Streamlit application (uses Ollama Cloud API)

set -e

echo "=========================================="
echo "Starting HR Resume Match Tool Container"
echo "=========================================="

echo "Configuration:"
echo "  Ollama Base URL: $OLLAMA_BASE_URL"
echo "  Model: $OLLAMA_MODEL_NAME"
echo "  API Key: ${OLLAMA_API_KEY:+Set} ${OLLAMA_API_KEY:-Not set}"
echo ""

echo "=========================================="
echo "Testing Ollama Cloud API connectivity..."
echo "=========================================="

# Test API connectivity
if curl -sf -H "Authorization: Bearer $OLLAMA_API_KEY" "$OLLAMA_BASE_URL/api/tags" > /dev/null 2>&1; then
    echo "✓ Ollama Cloud API is accessible"
else
    echo "⚠️  Ollama Cloud API test failed - this might be normal if API key is not set yet"
    echo "    The application will still start and health checks will handle connectivity"
fi
echo ""

echo "=========================================="
echo "Starting Streamlit application..."
echo "=========================================="
echo "Access the application at: http://localhost:8501"
echo ""

# Start Streamlit in foreground (this replaces the shell process)
exec streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0

#!/bin/sh
# Ollama Model Initialization Script
# This script pulls the qwen3:8b model on first container startup

set -e

echo "=========================================="
echo "Ollama Model Initialization"
echo "=========================================="

# Wait for Ollama service to be ready
echo "Waiting for Ollama service to be available..."
until curl -sf "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; do
    echo "Ollama service not ready yet, waiting..."
    sleep 5
done

echo "Ollama service is ready!"

# Check if model already exists
echo "Checking if model exists..."
if ollama list | grep -q "qwen3:8b"; then
    echo "✓ Model qwen3:8b already exists, skipping download"
else
    echo "Model not found, pulling qwen3:8b (this may take 15-30 minutes)..."
    echo "Download size: ~5GB"
    
    # Pull the model
    ollama pull qwen3:8b
    
    if [ $? -eq 0 ]; then
        echo "✓ Model qwen3:8b downloaded successfully!"
    else
        echo "✗ Failed to download model"
        exit 1
    fi
fi

# Verify model is available
echo "Verifying model availability..."
if ollama list | grep -q "qwen3:8b"; then
    echo "✓ Model verification successful!"
    ollama list
else
    echo "✗ Model verification failed"
    exit 1
fi

echo "=========================================="
echo "Initialization complete!"
echo "Ready to process resume matches"
echo "=========================================="

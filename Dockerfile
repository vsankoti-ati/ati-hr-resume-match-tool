# Stage 1: Get Ollama binary from official image
FROM ollama/ollama:latest AS ollama-stage

# Stage 2: Build the final application image with GPU support
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    curl \
    jq \
    procps \
    poppler-utils \
    libpoppler-cpp-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.11 /usr/bin/python

# Copy Ollama binary from the official image
COPY --from=ollama-stage /bin/ollama /bin/ollama

# Setup working directory
WORKDIR /resume-match-tool

# Copy and install Python dependencies
COPY requirements.txt /resume-match-tool/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /resume-match-tool/app/
COPY utils/ /resume-match-tool/utils/
COPY config/ /resume-match-tool/config/
COPY .env.template /resume-match-tool/.env

# Copy entrypoint script
COPY scripts/entrypoint.sh /resume-match-tool/entrypoint.sh
COPY scripts/diagnose-ollama.sh /resume-match-tool/diagnose-ollama.sh
RUN chmod +x /resume-match-tool/entrypoint.sh /resume-match-tool/diagnose-ollama.sh

# Create directory for Ollama models
RUN mkdir -p /root/.ollama

# Set environment variables (including GPU support)
ENV PYTHONUNBUFFERED=1 \
    OLLAMA_BASE_URL=http://localhost:11434 \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MODEL_NAME=qwen3:8b \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false\
    OLLAMA_MODELS=/root/.ollama/models \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Expose both Ollama and Streamlit ports
EXPOSE 11434 8501

# Define volume for persistent model storage
VOLUME ["/root/.ollama"]

# Use the entrypoint script that starts both Ollama and Streamlit
ENTRYPOINT ["/resume-match-tool/entrypoint.sh"]
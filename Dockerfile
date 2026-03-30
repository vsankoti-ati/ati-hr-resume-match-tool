# Build the final application image (Python only, no GPU/Ollama)
FROM python:3.11-slim

# Set working directory
WORKDIR /resume-match-tool

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpoppler-cpp-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

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
RUN chmod +x /resume-match-tool/entrypoint.sh

# Create results directory
RUN mkdir -p /resume-match-tool/results

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    OLLAMA_BASE_URL=https://ollama.com/api \
    OLLAMA_MODEL_NAME=qwen3.5:397b \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose Streamlit port
EXPOSE 8501

# Set entrypoint
ENTRYPOINT ["/resume-match-tool/entrypoint.sh"]

# Expose both Ollama and Streamlit ports
EXPOSE 11434 8501

# Define volume for persistent model storage
VOLUME ["/root/.ollama"]

# Use the entrypoint script that starts both Ollama and Streamlit
ENTRYPOINT ["/resume-match-tool/entrypoint.sh"]
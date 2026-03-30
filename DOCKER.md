# Docker Deployment Guide

This guide covers running the HR Resume Match Tool using Docker and Docker Compose.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- 10GB+ free disk space (for Qwen3 8B model)
- 8GB+ RAM (recommended for qwen3:8b)

## Quick Start

### 1. Build and Start Container

```bash
# Start the combined container (Ollama + Python app)
docker-compose up -d

# View logs
docker-compose logs -f hr-resume-app

# First run will download the model (5-10 minutes for ~5GB)
# Subsequent runs will start immediately using cached model
```

### 2. Access Application

Once initialized, access the application at:
- **Application UI**: http://localhost:8501
- **Ollama API**: http://localhost:11434

### 3. Stop Services

```bash
# Stop container
docker-compose down

# Stop and remove volumes (removes downloaded model)
docker-compose down -v
```

## Single-Container Architecture

The Docker setup now uses a **single combined container** for simplified deployment:

### hr-resume-app
- **Base Image**: `python:3.11-slim` + Ollama installation
- **Ports**: 
  - 8501 (Streamlit UI)
  - 11434 (Ollama API)
- **Volumes**: 
  - `ollama-models` (persistent model storage)
  - `results` (generated reports)
- **Services**: Runs both Ollama and Streamlit in one container
- **Model**: qwen3:8b (~5GB, 8B parameters)
- **Benefits**: 
  - Simpler architecture (no network overhead)
  - Easier Azure Container Apps deployment
  - Shared memory between services
  - Faster inter-process communication

## Container Startup Flow

```
┌──────────────────────────────────────┐
│      hr-resume-app Container         │
│                                      │
│  1. Start Ollama in background       │
│  2. Wait for Ollama health check     │
│  3. Pull model if not exists         │
│  4. Start Streamlit in foreground    │
│                                      │
│  ┌────────────┐   ┌──────────────┐  │
│  │   Ollama   │   │  Streamlit   │  │
│  │ Port 11434 │   │  Port 8501   │  │
│  └────────────┘   └──────────────┘  │
│         │               │            │
│         └───localhost───┘            │
│                                      │
│  Volume: /root/.ollama (models)      │
└──────────────────────────────────────┘
```

## Volume Mounts

### Persistent Model Storage
```yaml
volumes:
  - ollama-models:/root/.ollama  # Prevents re-downloading 5GB model
```

### Development Mode (with hot reload)
```yaml
volumes:
  - ./app:/app/app
  - ./utils:/app/utils
  - ./config:/app/config
  - results:/app/results
```

### Production Mode
Remove source code volume mounts to use code baked into Docker image:
```yaml
# Comment out development volumes for production
# volumes:
#   - ./app:/app/app
```

## Building Custom Image

### Build Locally
```bash
# Build combined image
docker build -t hr-resume-matcher:latest .

# Run container (standalone without docker-compose)
docker run -d \
  -p 8501:8501 \
  -p 11434:11434 \
  -v ollama-models:/root/.ollama \
  -v $(pwd)/results:/app/results \
  --name hr-resume-app \
  hr-resume-matcher:latest
```

### Build for Multiple Platforms (ARM + x86)
```bash
# Setup buildx
docker buildx create --use

# Build multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t youracr.azurecr.io/hr-resume-matcher:v1 \
  --push .
```

## Health Checks

The container health check verifies both services are running:

### Combined Health Check
```bash
# Check both Ollama and Streamlit
curl http://localhost:11434/api/tags && curl http://localhost:8501/_stcore/health
```

### Individual Service Checks
```bash
# Ollama API
curl http://localhost:11434/api/tags

# Streamlit UI
curl http://localhost:8501/_stcore/health
```

## Troubleshooting

### Model Download Fails
```bash
# Check container logs
docker-compose logs hr-resume-app

# Manually pull model
docker-compose exec hr-resume-app ollama pull qwen3:8b
```

### Connection Issues
```bash
# Verify container is running
docker-compose ps

# Check both services inside container
docker-compose exec hr-resume-app curl http://localhost:11434/api/tags
docker-compose exec hr-resume-app curl http://localhost:8501/_stcore/health

# Restart container
docker-compose restart
```

### Out of Memory
```bash
# Check container stats
docker stats hr-resume-matcher

# Increase Docker Desktop memory limit
# Settings → Resources → Memory → 16GB+

# Adjust resource limits in docker-compose.yaml
# deploy.resources.limits.memory: 16G
```

### Ollama Not Starting
```bash
# View detailed logs
docker-compose logs -f hr-resume-app

# Check entrypoint script execution
docker-compose exec hr-resume-app ps aux

# Verify Ollama installation
docker-compose exec hr-resume-app which ollama
docker-compose exec hr-resume-app ollama --version
```

## Environment Variables

Configure in `docker-compose.yaml` or `.env`:

```yaml
environment:
  - OLLAMA_BASE_URL=http://localhost:11434      # Use localhost in combined container
  - OLLAMA_HOST=0.0.0.0:11434                   # Ollama bind address
  - OLLAMA_MODEL_NAME=qwen3:8b                   # Can change to other models
  - OLLAMA_TIMEOUT=600
  - STREAMLIT_SERVER_PORT=8501
  - MAX_UPLOAD_SIZE_MB=200
```

## Performance Tuning

### Resource Limits
Configure in `docker-compose.yaml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 16G
    reservations:
      cpus: '2'
      memory: 8G
```

```yaml
services:
  ollama-service:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Model Quantization
Use smaller quantized models for lower memory:
```bash
# Instead of 32B, use smaller models
OLLAMA_MODEL_NAME=qwen3:8b         # ~5GB (recommended)
OLLAMA_MODEL_NAME=llama3.2:3b      # ~2GB (smaller/faster)
```

## Logs and Debugging

### View All Logs
```bash
docker-compose logs -f
```

### Service-Specific Logs
```bash
docker-compose logs -f ollama-service
docker-compose logs -f python-app
docker-compose logs -f ollama-init
```

### Execute Commands in Container
```bash
# Python app container
docker-compose exec python-app /bin/bash

# Ollama container
docker-compose exec ollama-service /bin/bash

# List models
docker-compose exec ollama-service ollama list
```

## Next Steps

- For Azure Container Apps deployment, see [Azure Deployment Guide](infrastructure/README.md)
- For production configuration, see [plan.md](plan.md)
- For development setup, see [README.md](README.md)

## Development Workflow

1. **Code Changes**: Edit files locally
2. **Hot Reload**: Streamlit auto-reloads (via volume mounts)
3. **Rebuild**: `docker-compose up --build` after dependency changes
4. **Test**: Access http://localhost:8501

## Production Deployment

For Azure Container Apps:
1. Build and push image to Azure Container Registry
2. Deploy using ARM template (see `infrastructure/azuredeploy.json`)
3. Configure workload profile for model memory requirements
4. Setup Azure Files volume mount for model persistence

See Phase 3 in [plan.md](plan.md) for complete deployment instructions.

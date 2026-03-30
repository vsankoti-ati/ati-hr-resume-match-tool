## Plan: Azure Container Apps HR Resume Matching Tool with Ollama Sidecar

Deploy a Python-based HR resume matching tool using Streamlit and Ollama qwen3:8b model as a multi-container Azure Container App with persistent storage for model files and generated reports.

---

## **CURRENT ACTIVE WORK: PDF Report Restructuring for HR Perspective**

**Status**: Planning Complete - Ready for Implementation

**Objective**: Restructure the PDF report from candidate-focused to HR-focused by changing recommendations to hiring decisions, adding interview questions, and converting verbose sections into compact tables to reduce page count while improving readability.

**Key Changes**:
1. **HR Recommendation Section** (replaces candidate recommendations)
   - Decision: Proceed to Interview | Consider with Reservations | Do Not Proceed
   - Reasoning and key considerations
   - Decision based on match thresholds: ≥70% Proceed, 50-69% Consider, <50% Do Not Proceed

2. **Interview Questions Section** (new)
   - Technical questions (3-5) - probe gaps and validate skills
   - Behavioral questions (3-5) - assess cultural fit
   - Two-column table format for easy scanning

3. **Compact Table Formats** (reduce page count by ~40%)
   - Matching Skills: 4-column table (Technical | Soft | Qualifications | Experience)
   - Detailed Matches: Wide table with one row per match (currently one table per match)
   - Gaps: Consolidated table (currently one table per gap)
   - Strengths: Consolidated table (currently one table per strength)

**Files to Modify**:
- `config/config.py` - Update AI prompt JSON schema
- `app/matcher.py` - Update field validation
- `utils/report_generator.py` - Restructure 5 sections

**Detailed Plan**: See `/memories/session/plan.md` for complete implementation steps, patterns, and verification checklist.

---

**Steps**

### Phase 1: Project Structure & Python Application
1. Create Python project structure with directories: `app/`, `templates/`, `utils/`, `config/`
2. Implement document processing module using PyPDF2, python-docx, and pdfplumber for PDF/Word parsing
3. Create Ollama client module with HTTP client to communicate with Ollama service at `http://localhost:11434`
4. Build matching engine that sends prompts to qwen3:8b for:
   - Overall match percentage calculation
   - Skills/qualifications comparison
   - Gap analysis (missing skills in profile)
   - Strength analysis (extra skills in profile)
   - Anomaly detection for discrepancies
5. Develop Streamlit UI with file upload, progress indicators, report display, and PDF export functionality
6. Create requirements.txt with: streamlit, PyPDF2, python-docx, pdfplumber, requests, reportlab

*Steps 2-6 can be done in parallel after step 1*

### Phase 2: Docker Multi-Container Configuration
7. Create Dockerfile for Python app with python:3.11-slim base, PDF processing dependencies, Streamlit on port 8501
8. Create docker-compose.yaml for local testing with ollama-service and python-app sharing localhost network and volumes
9. Create initialization script to pull qwen3:8b model on first container startup

*Depends on Phase 1*

### Phase 3: Azure Infrastructure - ARM Templates  
10. Create ARM template (`infrastructure/azuredeploy.json`) with:
    - **Storage Account**: Standard_GRS, 100GB file share named `ollama-models`
    - **Log Analytics Workspace**: 30-day retention for Container Apps logging
    - **Container Apps Environment**: Memory-Optimized E16 workload profile (4 vCPU, 32GB), Azure Files storage link, VNet integration
    - **Container App**: Two containers (ollama-service: 2 vCPU/24GB, python-app: 1 vCPU/2GB), volume mounts, external ingress on port 8501, health probes
11. Create parameters.json with configurable values: ACR URL, image tag, storage account name, location

*Steps 10-11 can be done in parallel with Phase 2*

### Phase 4: CI/CD & Deployment Preparation
12. Create .dockerignore excluding `.git/`, `__pycache__/`, `*.pyc`, `.env`, `venv/`
13. Create GitHub Actions workflow: build Docker image → push to ACR → deploy ARM template
14. Create deployment scripts: `scripts/deploy.sh` (ARM deployment wrapper), `scripts/init-model.sh` (pull qwen3:8b model via Azure CLI exec)

*Depends on Phases 2 and 3*

### Phase 5: Configuration & Environment Setup
15. Create .env.template documenting required variables: subscription ID, resource group, ACR name, model name
16. Create config/config.py with Ollama URL, model name, file size limits, timeouts
17. Add health check endpoints to Streamlit app for Container Apps probes
    - **17a**: Implemented comprehensive Ollama health monitoring (`utils/health_check.py`)
      - `check_ollama_health()`: Fast health check with 5s timeout, returns readiness status and response time
      - `wait_for_ollama_ready()`: Polling function for startup initialization (max 5 minutes)
      - `get_model_info()`: Model availability verification and metadata
    - **17b**: Integrated health checks into Streamlit UI (`app/main.py`)
      - Blocking health check after authentication (prevents usage if Ollama not ready)
      - Live status indicator in sidebar with response time metrics
      - Startup error screen with retry button for cold starts
      - Loaded models display with size information
    - **Purpose**: Critical for Azure Container Apps serverless GPU deployment where cold starts can take 2-5 minutes
18. Add Azure AD authentication for production deployment
    - **18a**: Configure Azure AD app registration with OAuth2 authorization code flow
    - **18b**: Implement MSAL authentication in `utils/auth_service.py` with token validation
    - **18c**: Create login UI and authentication wrapper in `app/login.py` and `app/auth_wrapper.py`
    - **18d**: Add authentication configuration in `config/auth_config.py`
    - **Status**: ✅ Completed - Full Azure AD integration with OAuth2, logout flow, and mock auth for local dev

*Parallel with Phase 4*

**Relevant Files**

Project structure to create:

I don't currently have file editing tools enabled. Here's the complete plan content that you can save to plan.md:

/Users/vishnusankoti/ATI/ati-hr-resume-match-tool/
├── app/
│ ├── main.py — Streamlit UI with file upload, report display, PDF export
│ └── matcher.py — Core matching logic orchestration
├── utils/
│ ├── document_parser.py — PDF/Word parsing with PyPDF2, python-docx
│ ├── ollama_client.py — HTTP client for Ollama API at localhost:11434
│ └── report_generator.py — PDF report generation with reportlab
├── config/
│ └── config.py — Environment configuration and constants
├── infrastructure/
│ ├── azuredeploy.json — ARM template with Storage, Container App Environment, Container App
│ └── parameters.json — Deployment parameters (ACR URL, location, etc.)
├── scripts/
│ ├── deploy.sh — Deployment automation script
│ └── init-model.sh — Model initialization in Ollama container
├── Dockerfile — Python app container definition
├── docker-compose.yaml — Local multi-container testing setup
├── requirements.txt — Python dependencies (currently exists, needs updating)
├── .dockerignore — Docker build exclusions
└── .env.template — Environment variables template



Key architecture patterns to implement:
- **Document parser**: Extract text from PDF (pdfplumber for complex layouts) and Word (python-docx), preprocess to clean text
- **Ollama client**: POST requests to `/api/generate` endpoint with model name and prompt, stream responses for real-time UI updates
- **Matching prompts**: Structured prompts for each report section (5 separate API calls or single comprehensive prompt)
- **Streamlit layout**: Use `st.file_uploader`, `st.progress`, `st.markdown` for report display, `st.download_button` for PDF export
- **ARM template**: Use nested resource dependencies - Storage Account → File Share → Container Environment → Container App

**Verification**

1. **Local Docker testing**: Run `docker-compose up`, verify Ollama on port 11434, Streamlit on 8501, upload test PDFs, confirm report generation
2. **ARM template validation**: Run `az deployment group validate --template-file infrastructure/azuredeploy.json --parameters @infrastructure/parameters.json`
3. **Azure deployment**: Deploy ARM template, check Container App status: `az containerapp show --resource-group <rg> --name hr-resume-matcher`
4. **Model initialization**: Exec into Ollama container and verify qwen3:8b model is pulled: `az containerapp exec --name hr-resume-matcher --container ollama-service --command "ollama list"`
5. **Volume mount verification**: Check Azure Files share has `/root/.ollama/models` directory with model files
6. **End-to-end test**: Access Container App ingress URL, upload sample resume PDF and job description PDF, verify all 5 report sections generate correctly
7. **Probe health**: Monitor Container App metrics in Azure Portal - ensure liveness/startup probes are passing
8. **Storage persistence**: Restart Container App, verify model doesn't need re-download (persisted in Azure Files)

**Decisions & Assumptions**

- **Workload Profile Choice**: Using Consumption profile with 4 vCPU and 8GB memory as qwen3:8b (~5GB) fits comfortably. This provides good performance without the cost of dedicated workload profiles.
- **Storage Strategy**: Azure Files for model persistence (survives restarts); EmptyDir volumes excluded initially for simplicity (can add later for inference caching).
- **Model Selection**: Using qwen3:8b for optimal balance of performance and resource requirements.
- **Network Communication**: Containers communicate via `localhost` (same pod networking in Container Apps) - no service mesh overhead.
- **Scaling Strategy**: Initial min count = 1 (always-on to avoid model reload), max count = 3 for high traffic scenarios.
- **Cost Consideration**: Dedicated workload profile incurs fixed costs even at idle - evaluate Consumption profile with 8GB max if willing to accept cold start latency and smaller quantized models.

**Limitations & Exclusions**

- **Authentication**: Initial implementation has no authentication on Streamlit UI - add Azure AD integration in future iteration if needed.
- **GPU Support**: Azure Container Apps doesn't support GPU workload profiles yet (as of March 2026) - CPU inference only, expect slower response times (30-60s per analysis).
- **Monitoring**: Basic Container Apps logs only - advanced APM (Application Insights custom metrics for inference latency) excluded from initial scope.
- **Multi-tenancy**: Single Container App instance - no per-user resource isolation.

**Further Considerations**

1. **Model Loading Strategy**: qwen3:8b takes 1-3 minutes to load on first request in Ollama. Should we:
   - **Option A**: Pre-load model in Dockerfile CMD with `ollama run` command (increases startup time but guarantees readiness)
   - **Option B**: Lazy load on first user request (faster startup, first user waits)
   - **Option C**: Use startup probe with 5-minute initial delay and init container pattern
   - **Recommendation**: ✅ **Implemented Option C with UI Enhancement** - Added comprehensive health monitoring that:
     - Blocks user access until Ollama and model are ready (prevents failed requests)
     - Displays clear startup messages for cold start scenarios (Azure serverless GPU)
     - Provides live status indicators in sidebar with response time metrics
     - Includes retry mechanism for transient failures
   - **Note**: Using qwen3:8b model (confirmed working)

2. **Health Monitoring Implementation**: ✅ **Completed**
   - Created `utils/health_check.py` with production-ready health monitoring functions
   - Integrated blocking health check in `app/main.py` after authentication
   - Added live sidebar status indicators with model information
   - Provides clear error messages for operations team debugging
   - Response time metrics for performance monitoring

3. **File Upload Size Limits**: Streamlit default is 200MB. For large resume portfolios:
   - Keep default 200MB or increase to 500MB?
   - Store uploaded files temporarily in Azure Files vs in-memory?
   - **Recommendation**: 200MB limit with in-memory processing initially, add Azure Files temp storage if issues arise

3. **Report Generation Approach**: 5 separate Ollama API calls (one per report section) vs single comprehensive prompt:
   - **Option A**: 5 calls - more granular, easier to retry failures, slower (5x latency)
   - **Option B**: 1 call with structured output - faster, requires careful prompt engineering, harder to debug
   - **Recommendation**: Option B with JSON-structured output, fallback to Option A if parsing fails

4. **ARM Template vs Terraform vs Bicep**:
   - Requirement specifies ARM template - confirm if Bicep (ARM DSL) is acceptable, which offers cleaner syntax and better type checking
   - **Recommendation**: Use Bicep, compile to ARM JSON for final deployment if strict ARM required
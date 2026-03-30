# ATI HR Resume Match Tool

AI-powered resume matching tool that analyzes candidate profiles against job descriptions using Ollama Cloud API and Qwen3.5 Cloud model.

## Features

- 📊 **Overall Match Scoring**: Get an instant percentage match between profile and job description
- 🎯 **Detailed Skill Analysis**: Breakdown of matching technical skills, soft skills, qualifications, and experience
- ⚠️ **Gap Identification**: Identify missing skills with suggestions for acquisition
- 💪 **Strength Highlighting**: Discover unique strengths and how to emphasize them
- 🚨 **Anomaly Detection**: Flag discrepancies in dates, titles, or qualifications
- 📄 **PDF Export**: Generate professional PDF reports
- 🎨 **Modern UI**: Clean, intuitive Streamlit interface
- 🔒 **Privacy Protection**: Automatic PII masking before sending data to cloud AI services

## Privacy & Security

This application prioritizes candidate privacy by automatically masking personally identifiable information (PII) before sending resume data to Ollama Cloud for analysis.

### PII Masking Features

- **Automatic Detection**: Uses Microsoft Presidio to identify sensitive information including:
  - Names and personal identifiers
  - Email addresses and phone numbers
  - Physical addresses and locations
  - Social security numbers and IDs
  - Financial information
  - Medical data

- **Configurable**: PII masking can be enabled/disabled via environment variables
- **Fallback Method**: Includes regex-based masking as fallback if Presidio is unavailable
- **Transparency**: Analysis results include PII masking statistics for audit purposes

### Configuration

```bash
# Enable/disable PII masking
ENABLE_PII_MASKING=true

# Choose masking method
PII_MASKING_METHOD=presidio  # 'presidio' (recommended) or 'regex'
```

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama Cloud API key (get from https://ollama.com)
- Docker and Docker Compose

### Installation

1. **Clone the repository** (or navigate to project directory)
```bash
cd ati-hr-resume-match-tool
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.template .env
# Edit .env and add your Ollama Cloud API key:
# OLLAMA_API_KEY=your_api_key_here
```

4. **Run the application**
```bash
streamlit run app/main.py
```

5. **Open browser**
Navigate to `http://localhost:8501`

## Usage

1. **Upload Documents**
   - Upload candidate profile (PDF or Word)
   - Upload job description (PDF or Word)

2. **Analyze**
   - Click "Analyze Match" button
   - Wait 30-60 seconds for AI analysis

3. **Review Results**
   - Switch to "Results" tab
   - View detailed match analysis
   - Export PDF report if needed

## Project Structure

```
ati-hr-resume-match-tool/
├── app/
│   ├── main.py              # Streamlit UI
│   └── matcher.py           # Matching engine
├── utils/
│   ├── document_parser.py   # PDF/Word parsing
│   ├── ollama_client.py     # Ollama API client
│   └── report_generator.py  # PDF generation
├── config/
│   └── config.py            # Configuration
├── requirements.txt         # Dependencies
└── .env.template           # Environment template
```

## Configuration

Environment variables (in `.env`):

```bash
# Ollama Cloud
OLLAMA_BASE_URL=https://ollama.com/api
OLLAMA_API_KEY=your_api_key_here
OLLAMA_MODEL_NAME=qwen3.5:397b
OLLAMA_TIMEOUT=600

# PII Masking (Privacy Protection)
ENABLE_PII_MASKING=true
PII_MASKING_METHOD=presidio  # 'presidio' (recommended) or 'regex'

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# File Upload
MAX_UPLOAD_SIZE_MB=200

# Azure AD Authentication
ENABLE_AUTH=false  # Set to true for production
AZURE_AD_TENANT_ID=your-tenant-id-here
AZURE_AD_CLIENT_ID=your-client-id-here
AZURE_AD_CLIENT_SECRET=your-client-secret-here
AZURE_AD_REDIRECT_URI=http://localhost:8501
```

## Azure AD Authentication Setup

The application supports Azure AD authentication for enterprise deployments. For local development, authentication can be disabled using mock authentication.

### Local Development (No Azure AD Required)

Set `ENABLE_AUTH=false` in your `.env` file:
```bash
ENABLE_AUTH=false
```

The application will automatically authenticate you as `dev@example.com` with admin role. No login page will be shown.

### Production Setup (Azure AD)

#### Step 1: Register Application in Azure AD

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure the app:
   - **Name**: `ATI HR Resume Match Tool`
   - **Supported account types**: Select appropriate option (e.g., "Accounts in this organizational directory only")
   - **Redirect URI**: Select "Web" and enter:
     - For local: `http://localhost:8501`
     - For Azure Container Apps: `https://your-app-name.azurecontainerapps.io`
5. Click **Register**

#### Step 2: Configure Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description (e.g., "HR Tool Production")
4. Select expiration period (recommended: 6 months or 1 year)
5. Click **Add**
6. **IMPORTANT**: Copy the secret value immediately (it won't be shown again)

#### Step 3: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Verify that **User.Read** (Microsoft Graph) is present (added by default)
3. Click **Grant admin consent** if required by your organization

#### Step 4: Update Environment Variables

Update your `.env` file with the values from Azure AD:

```bash
ENABLE_AUTH=true
AZURE_AD_TENANT_ID=<your-tenant-id>       # From "Overview" → "Directory (tenant) ID"
AZURE_AD_CLIENT_ID=<your-client-id>       # From "Overview" → "Application (client) ID"
AZURE_AD_CLIENT_SECRET=<your-secret>      # From "Certificates & secrets"
AZURE_AD_REDIRECT_URI=http://localhost:8501
```

#### Step 5: Test Authentication

1. Start the application: `streamlit run app/main.py`
2. Navigate to `http://localhost:8501`
3. You should see the login page with "Sign in with Microsoft" button
4. Click the button to authenticate with your Azure AD account
5. After successful login, you'll be redirected to the main application
6. Your name and email will appear in the sidebar with a "Sign Out" button

### Security Best Practices

- **Never commit** `.env` file or client secrets to version control
- **Rotate client secrets** every 6-12 months
- Use **Azure Key Vault** for production secret storage
- Configure **Conditional Access policies** in Azure AD for additional security
- Review **sign-in logs** in Azure AD regularly
- Use **different app registrations** for dev, staging, and production

### Troubleshooting Authentication

#### "Login failed" Error
- Verify `AZURE_AD_TENANT_ID`, `AZURE_AD_CLIENT_ID`, and `AZURE_AD_CLIENT_SECRET` are correct
- Check that the redirect URI in Azure AD matches your `.env` setting exactly
- Ensure client secret has not expired

#### "Invalid redirect URI" Error
- The redirect URI must be registered in Azure AD app registration
- For local: `http://localhost:8501` (no trailing slash)
- For Azure: `https://your-app-name.azurecontainerapps.io`

#### Session Expires Immediately
- Check system clock is synchronized
- Verify JWT token is not being blocked by network policies
- Review browser console for errors

#### Mock Authentication Not Working
- Verify `ENABLE_AUTH=false` (not "False" or "0")
- Check that `config/auth_config.py` is present
- Restart the application after changing `.env`

## Docker Deployment

See [plan.md](plan.md) for Docker and Azure Container Apps deployment instructions.

## Troubleshooting

### Ollama Cloud Connection Issues
```bash
# Check if Ollama Cloud API is accessible
curl -H "Authorization: Bearer YOUR_API_KEY" https://ollama.com/api/version

# Test model inference
curl -X POST https://ollama.com/api/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3.5:397b", "prompt": "Hello", "stream": false}'
```

### API Key Issues
- Ensure `OLLAMA_API_KEY` environment variable is set
- Verify API key is valid and has credits
- Check API key format (should start with appropriate prefix)

### PDF Parsing Issues
- Ensure documents are not encrypted
- Try different PDF formats if parsing fails
- Check document has actual text (not scanned images)

## Development Status

- ✅ Phase 1: Python Application (Complete)
- 🔄 Phase 2: Docker Configuration (Pending)
- 🔄 Phase 3: Azure ARM Templates (Pending)
- 🔄 Phase 4: CI/CD Setup (Pending)

See [progress.md](progress.md) for detailed implementation status.

## Requirements

- Python 3.11+
- Ollama with Qwen3 8B model
- 4GB+ RAM (for model inference)
- Modern web browser

## License

Copyright © 2026 ATI

## Support

For issues or questions, please refer to [plan.md](plan.md) for detailed documentation.

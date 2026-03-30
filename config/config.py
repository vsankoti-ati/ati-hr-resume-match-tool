"""
Configuration module for HR Resume Matching Tool
Contains environment variables, constants, and application settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'https://ollama.com/api')
    OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', '')
    OLLAMA_MODEL_NAME = os.getenv('OLLAMA_MODEL_NAME', 'qwen3.5:397b')
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '600'))  # 10 minutes default
    
    # Streamlit Configuration
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '200'))
    MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc']
    
    # PII Masking Configuration
    ENABLE_PII_MASKING = os.getenv('ENABLE_PII_MASKING', 'true').lower() == 'true'
    PII_MASKING_METHOD = os.getenv('PII_MASKING_METHOD', 'presidio')  # 'presidio' or 'regex'
    REPORT_TITLE = "HR Resume Match Analysis Report"
    REPORT_AUTHOR = "ATI HR Resume Match Tool"
    
    # Analysis Configuration
    MATCH_THRESHOLD_EXCELLENT = 80  # Match percentage >= 80% is excellent
    MATCH_THRESHOLD_GOOD = 60       # Match percentage >= 60% is good
    MATCH_THRESHOLD_FAIR = 40       # Match percentage >= 40% is fair
    
    # Prompts Configuration
    SYSTEM_PROMPT = """You are an expert HR analyst specializing in resume and job description matching. 
Your task is to perform thorough analysis comparing candidate profiles with job descriptions. 
Provide detailed, actionable insights with specific examples and percentages."""
    
    @staticmethod
    def get_analysis_prompt(profile_text: str, job_description_text: str) -> str:
        """
        Generate comprehensive analysis prompt for Ollama
        
        Args:
            profile_text: Extracted text from candidate profile
            job_description_text: Extracted text from job description
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze the following candidate profile against the job description and provide a comprehensive match report.

**CANDIDATE PROFILE:**
{profile_text}

**JOB DESCRIPTION:**
{job_description_text}

**REQUIRED ANALYSIS (Return as JSON):**
Provide your analysis in the following JSON structure:

{{
  "overall_match_percentage": <number between 0-100>,
  "match_summary": "<2-3 sentence summary of overall fit>",
  
  "matching_skills": {{
    "technical_skills": ["<skill1>", "<skill2>", ...],
    "soft_skills": ["<skill1>", "<skill2>", ...],
    "qualifications": ["<qual1>", "<qual2>", ...],
    "experience_areas": ["<area1>", "<area2>", ...]
  }},
  
  "detailed_matches": [
    {{
      "category": "<Technical Skills|Soft Skills|Qualifications|Experience>",
      "item": "<specific skill/qualification/experience>",
      "profile_evidence": "<quote or reference from profile>",
      "jd_requirement": "<quote or reference from job description>",
      "match_strength": "<Strong|Moderate|Weak>"
    }}
  ],
  
  "gaps_in_profile": [
    {{
      "requirement": "<what's missing>",
      "importance": "<Critical|Important|Nice-to-have>",
      "suggestion": "<how candidate can acquire this skill/qualification>",
      "timeline": "<estimated time to acquire>"
    }}
  ],
  
  "profile_strengths": [
    {{
      "skill_or_experience": "<what candidate has that's valuable>",
      "relevance_to_jd": "<how it relates to job>",
      "highlight_strategy": "<how to emphasize in application/interview>"
    }}
  ],
  
  "anomalies": [
    {{
      "type": "<Job Title Mismatch|Date Inconsistency|Qualification Discrepancy|Experience Gap|Other>",
      "description": "<what the anomaly is>",
      "severity": "<High|Medium|Low>",
      "recommendation": "<what to do about it>"
    }}
  ],
  
  "hr_recommendation": {{
    "decision": "<Proceed to Interview|Consider with Reservations|Do Not Proceed>",
    "reasoning": "<2-3 sentence explanation based on match percentage, gaps, and strengths>",
    "key_considerations": ["<consideration1>", "<consideration2>", "<consideration3>"]
  }},
  
  "interview_questions": {{
    "technical_questions": ["<question1>", "<question2>", "<question3>"],
    "behavioral_questions": ["<question1>", "<question2>", "<question3>"]
  }}
}}

**INSTRUCTIONS FOR HR RECOMMENDATION:**
- Use "Proceed to Interview" if overall_match_percentage >= 70% and no critical gaps
- Use "Consider with Reservations" if overall_match_percentage between 50-69% or has important gaps that can be addressed
- Use "Do Not Proceed" if overall_match_percentage < 50% or has multiple critical gaps
- Reasoning should explain the decision based on key factors from the analysis
- Key considerations should highlight 3-5 specific points HR should note about this candidate

**INSTRUCTIONS FOR INTERVIEW QUESTIONS:**
- Generate 3-5 technical questions that probe gaps identified and validate claimed skills from the profile
- Generate 3-5 behavioral questions that assess cultural fit, soft skills, and alignment with job requirements
- Questions should be specific to this candidate's profile and the job description, not generic
- Technical questions should be challenging but fair based on the role's requirements
- Behavioral questions should use STAR method format (Situation, Task, Action, Result)

Ensure all percentages are realistic and based on the actual content. Provide specific examples and evidence from both documents."""

    @staticmethod
    def validate_config():
        """Validate configuration settings"""
        errors = []
        
        if not Config.OLLAMA_BASE_URL:
            errors.append("OLLAMA_BASE_URL is not set")
            
        if not Config.OLLAMA_MODEL_NAME:
            errors.append("OLLAMA_MODEL_NAME is not set")
            
        if Config.MAX_UPLOAD_SIZE_MB <= 0:
            errors.append("MAX_UPLOAD_SIZE_MB must be positive")
            
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True


# Validate configuration on import
Config.validate_config()

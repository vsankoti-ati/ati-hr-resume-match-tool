"""
Matching Engine Module
Orchestrates the resume matching analysis process
"""
import logging
from typing import Dict, Any, Optional, Tuple
from utils.document_parser import DocumentParser
from utils.ollama_client import OllamaClient
from utils.pii_masker import mask_pii_in_text
from config.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchingEngine:
    """Engine for matching resumes against job descriptions"""
    
    def __init__(self):
        """Initialize the matching engine"""
        self.parser = DocumentParser()
        self.ollama_client = OllamaClient()
        logger.info("Matching engine initialized")
    
    def check_system_health(self) -> Tuple[bool, str]:
        """
        Check if all required services are available
        
        Returns:
            Tuple of (is_healthy, status_message)
        """
        # Check Ollama service
        if not self.ollama_client.health_check():
            return False, "Ollama service is not available"
        
        # Check if model exists
        if not self.ollama_client.check_model_exists():
            return False, f"Model {Config.OLLAMA_MODEL_NAME} is not available"
        
        return True, "All systems operational"
    
    def parse_documents(
        self,
        profile_bytes: bytes,
        profile_filename: str,
        jd_bytes: bytes,
        jd_filename: str
    ) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
        """
        Parse both profile and job description documents
        
        Args:
            profile_bytes: Profile document bytes
            profile_filename: Profile document filename
            jd_bytes: Job description document bytes
            jd_filename: Job description filename
            
        Returns:
            Tuple of (profile_data, jd_data, error_message)
        """
        logger.info("Parsing documents...")
        
        # Parse profile
        profile_data = self.parser.parse_document(profile_bytes, profile_filename)
        if not profile_data:
            return None, None, f"Failed to parse profile document: {profile_filename}"
        
        # Validate profile
        is_valid, error_msg = self.parser.validate_extraction(profile_data, min_words=50)
        if not is_valid:
            return None, None, f"Profile validation failed: {error_msg}"
        
        # Parse job description
        jd_data = self.parser.parse_document(jd_bytes, jd_filename)
        if not jd_data:
            return None, None, f"Failed to parse job description: {jd_filename}"
        
        # Validate job description
        is_valid, error_msg = self.parser.validate_extraction(jd_data, min_words=30)
        if not is_valid:
            return None, None, f"Job description validation failed: {error_msg}"
        
        logger.info(f"Profile: {profile_data['word_count']} words, JD: {jd_data['word_count']} words")
        return profile_data, jd_data, None
    
    def analyze_match(
        self,
        profile_text: str,
        jd_text: str,
        stream: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Analyze match between profile and job description
        
        Args:
            profile_text: Extracted profile text
            jd_text: Extracted job description text
            stream: Whether to stream responses
            
        Returns:
            Tuple of (analysis_result, error_message)
        """
        logger.info("Starting match analysis...")
        
        try:
            # Mask PII in profile and job description text before sending to Ollama Cloud
            masked_profile_text = profile_text
            masked_jd_text = jd_text
            profile_pii_stats = {}
            jd_pii_stats = {}
            total_pii_masked = 0
            
            if Config.ENABLE_PII_MASKING:
                logger.info("PII masking enabled - masking sensitive data before analysis...")
                
                # Mask PII in profile text
                masked_profile_text, profile_pii_stats = mask_pii_in_text(
                    profile_text, 
                    method=Config.PII_MASKING_METHOD
                )
                
                # Mask PII in job description text
                masked_jd_text, jd_pii_stats = mask_pii_in_text(
                    jd_text, 
                    method=Config.PII_MASKING_METHOD
                )
                
                total_pii_masked = sum(profile_pii_stats.values()) + sum(jd_pii_stats.values())
                
                if total_pii_masked > 0:
                    logger.info(f"Total PII instances masked: {total_pii_masked} ({profile_pii_stats}, {jd_pii_stats})")
                else:
                    logger.info("No PII detected in documents")
            else:
                logger.info("PII masking disabled - proceeding with original text")
            
            # Perform analysis using Ollama with masked text
            analysis_result = self.ollama_client.analyze_resume(
                profile_text=masked_profile_text,
                job_description_text=masked_jd_text,
                stream=stream
            )
            
            if not analysis_result:
                return None, "Failed to get analysis from Ollama"
            
            # Add PII masking information to the result for transparency
            analysis_result['_pii_masking'] = {
                'enabled': Config.ENABLE_PII_MASKING,
                'method': Config.PII_MASKING_METHOD if Config.ENABLE_PII_MASKING else None,
                'profile_pii_stats': profile_pii_stats,
                'jd_pii_stats': jd_pii_stats,
                'total_masked': total_pii_masked
            }
            
            # Validate analysis result structure
            required_fields = [
                'overall_match_percentage',
                'match_summary',
                'matching_skills',
                'detailed_matches',
                'gaps_in_profile',
                'profile_strengths',
                'anomalies',
                'hr_recommendation',
                'interview_questions'
            ]
            
            missing_fields = [field for field in required_fields if field not in analysis_result]
            if missing_fields:
                logger.warning(f"Analysis result missing fields: {missing_fields}")
                # Fill in missing fields with defaults
                for field in missing_fields:
                    if field == 'overall_match_percentage':
                        analysis_result[field] = 0
                    elif field == 'match_summary':
                        analysis_result[field] = "Analysis incomplete"
                    elif field in ['matching_skills']:
                        analysis_result[field] = {}
                    elif field == 'hr_recommendation':
                        analysis_result[field] = {
                            'decision': 'Consider with Reservations',
                            'reasoning': 'Analysis incomplete - manual review required',
                            'key_considerations': ['Incomplete analysis data']
                        }
                    elif field == 'interview_questions':
                        analysis_result[field] = {
                            'technical_questions': ['Review technical skills during interview'],
                            'behavioral_questions': ['Discuss work experience and approach']
                        }
                    else:
                        analysis_result[field] = []
            
            logger.info(f"Analysis complete: {analysis_result['overall_match_percentage']}% match")
            return analysis_result, None
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return None, f"Analysis error: {str(e)}"
    
    def process_match_request(
        self,
        profile_bytes: bytes,
        profile_filename: str,
        jd_bytes: bytes,
        jd_filename: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Complete end-to-end processing of match request
        
        Args:
            profile_bytes: Profile document bytes
            profile_filename: Profile document filename
            jd_bytes: Job description document bytes
            jd_filename: Job description filename
            
        Returns:
            Tuple of (analysis_result, error_message)
        """
        # Check system health
        is_healthy, health_msg = self.check_system_health()
        if not is_healthy:
            return None, health_msg
        
        # Parse documents
        profile_data, jd_data, parse_error = self.parse_documents(
            profile_bytes, profile_filename,
            jd_bytes, jd_filename
        )
        
        if parse_error:
            return None, parse_error
        
        # Perform analysis
        analysis_result, analysis_error = self.analyze_match(
            profile_data['text'],
            jd_data['text']
        )
        
        if analysis_error:
            return None, analysis_error
        
        # Add metadata to result
        analysis_result['metadata'] = {
            'profile_filename': profile_filename,
            'jd_filename': jd_filename,
            'profile_word_count': profile_data['word_count'],
            'jd_word_count': jd_data['word_count'],
            'profile_parsing_method': profile_data['method'],
            'jd_parsing_method': jd_data['method']
        }
        
        return analysis_result, None
    
    def get_match_grade(self, percentage: float) -> str:
        """
        Get qualitative grade for match percentage
        
        Args:
            percentage: Match percentage (0-100)
            
        Returns:
            Grade string
        """
        if percentage >= Config.MATCH_THRESHOLD_EXCELLENT:
            return "Excellent Match"
        elif percentage >= Config.MATCH_THRESHOLD_GOOD:
            return "Good Match"
        elif percentage >= Config.MATCH_THRESHOLD_FAIR:
            return "Fair Match"
        else:
            return "Poor Match"


# Create singleton instance
_engine = None


def get_matching_engine() -> MatchingEngine:
    """Get or create singleton matching engine instance"""
    global _engine
    if _engine is None:
        _engine = MatchingEngine()
    return _engine

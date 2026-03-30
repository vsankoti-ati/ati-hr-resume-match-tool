"""
Ollama Client Module
Handles communication with Ollama API for LLM inference
"""
import json
import requests
import logging
from typing import Optional, Dict, Any, Generator
from config.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(
        self, 
        base_url: str = None, 
        model_name: str = None,
        timeout: int = None
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Base URL for Ollama API (default from config)
            model_name: Name of the model to use (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.base_url = (base_url or Config.OLLAMA_BASE_URL).rstrip('/')
        self.model_name = model_name or Config.OLLAMA_MODEL_NAME
        self.timeout = timeout or Config.OLLAMA_TIMEOUT
        
        logger.info(f"Initialized Ollama client: {self.base_url}, model: {self.model_name}")
    
    def health_check(self) -> bool:
        """
        Check if Ollama service is available
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    def list_models(self) -> Optional[list]:
        """
        List available models
        
        Returns:
            List of model names or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                logger.info(f"Available models: {models}")
                return models
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return None
    
    def check_model_exists(self, model_name: str = None) -> bool:
        """
        Check if a specific model is available
        
        Args:
            model_name: Model name to check (default: configured model)
            
        Returns:
            True if model exists, False otherwise
        """
        model = model_name or self.model_name
        models = self.list_models()
        
        if models is None:
            return False
        
        return model in models
    
    def generate(
        self, 
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False
    ) -> Optional[str]:
        """
        Generate text completion using Ollama
        
        Args:
            prompt: User prompt for generation
            system_prompt: System prompt to set context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Generated text or None if failed
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            logger.info(f"Generating with model {self.model_name}, temp={temperature}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            
            if response.status_code == 200:
                if stream:
                    # Handle streaming response
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            json_response = json.loads(line)
                            if 'response' in json_response:
                                full_response += json_response['response']
                    return full_response
                else:
                    # Handle non-streaming response
                    data = response.json()
                    return data.get('response', '')
            else:
                logger.error(f"Generation failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out after {self.timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            return None
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Generator[str, None, None]:
        """
        Generate text with streaming for real-time updates
        
        Args:
            prompt: User prompt for generation
            system_prompt: System prompt to set context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of generated text
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line)
                            if 'response' in json_response:
                                yield json_response['response']
                        except json.JSONDecodeError:
                            continue
            else:
                logger.error(f"Streaming failed: {response.status_code}")
                yield ""
                
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            yield ""
    
    def analyze_resume(
        self,
        profile_text: str,
        job_description_text: str,
        stream: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze resume against job description
        
        Args:
            profile_text: Extracted text from candidate profile
            job_description_text: Extracted text from job description
            stream: Whether to stream the response
            
        Returns:
            Parsed analysis results as dictionary or None if failed
        """
        # Generate the analysis prompt
        prompt = Config.get_analysis_prompt(profile_text, job_description_text)
        
        # Get response from Ollama
        logger.info("Starting resume analysis...")
        response_text = self.generate(
            prompt=prompt,
            system_prompt=Config.SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent structured output
            max_tokens=4000,
            stream=stream
        )
        
        if not response_text:
            logger.error("No response from Ollama")
            return None
        
        # Try to parse JSON from response
        try:
            # Find JSON in response (it might be wrapped in markdown code blocks)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis_result = json.loads(json_str)
                logger.info("Successfully parsed analysis results")
                return analysis_result
            else:
                logger.error("No JSON found in response")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}...")
            return None
    
    def get_model_info(self, model_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model
        
        Args:
            model_name: Name of model to query (default: configured model)
            
        Returns:
            Model information dictionary or None if failed
        """
        model = model_name or self.model_name
        
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get model info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return None


# Create a singleton instance for convenience
_default_client = None


def get_ollama_client() -> OllamaClient:
    """Get or create default Ollama client instance"""
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client

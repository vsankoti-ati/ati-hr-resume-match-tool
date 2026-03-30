"""
Ollama Health Check Module
Provides health monitoring for Ollama AI service
"""
import requests
import time
import logging
from typing import Tuple, Dict
from config.config import Config

logger = logging.getLogger(__name__)


def test_model_inference() -> Tuple[bool, str, int]:
    """
    Test actual model inference to ensure model is loaded and ready
    
    Returns:
        Tuple of (success, error_message, response_time_ms)
    """
    start = time.time()
    
    try:
        payload = {
            "model": Config.OLLAMA_MODEL_NAME,
            "prompt": "Reply with just 'OK'",
            "stream": False,
            "options": {
                "num_predict": 5,
                "temperature": 0.1
            }
        }
        
        response = requests.post(
            f"{Config.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=30  # 30 second timeout for inference test
        )
        
        response_time_ms = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            if 'response' in data:
                logger.info(f"Model inference test passed in {response_time_ms}ms")
                return True, "", response_time_ms
            else:
                error_msg = "Response missing 'response' field"
                logger.warning(f"Inference test failed: {error_msg}")
                return False, error_msg, response_time_ms
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error(f"Inference test failed: {error_msg}")
            return False, error_msg, response_time_ms
            
    except requests.exceptions.Timeout:
        response_time_ms = int((time.time() - start) * 1000)
        logger.warning(f"Inference test timeout after {response_time_ms}ms")
        return False, "Inference timeout - model may be loading", response_time_ms
        
    except Exception as e:
        response_time_ms = int((time.time() - start) * 1000)
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Inference test error: {error_msg}")
        return False, error_msg, response_time_ms


def check_ollama_health() -> Tuple[bool, str, Dict]:
    """
    Check Ollama service health and model availability with inference test
    
    Returns:
        Tuple of (is_healthy, message, details)
        - is_healthy: Boolean indicating if service is ready for inference
        - message: Human-readable status message
        - details: Dictionary with diagnostic information
    """
    details = {
        "reachable": False,
        "model_available": False,
        "inference_ready": False,
        "response_time_ms": None,
        "models_loaded": [],
        "error": None
    }
    
    start = time.time()
    
    # Step 1: Check if Ollama API is reachable
    try:
        response = requests.get(
            f"{Config.OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )
        details["response_time_ms"] = int((time.time() - start) * 1000)
        details["reachable"] = response.status_code == 200
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            details["models_loaded"] = model_names
            details["model_available"] = Config.OLLAMA_MODEL_NAME in model_names
            
            if not details["model_available"]:
                available_str = ', '.join(model_names[:3]) if model_names else "None"
                logger.warning(f"Model {Config.OLLAMA_MODEL_NAME} not found. Available: {available_str}")
                return False, f"⚠️ Model not loaded. Available: {available_str}", details
            
            # Step 2: Test actual inference
            inference_ok, error_msg, inference_time = test_model_inference()
            details["inference_ready"] = inference_ok
            details["response_time_ms"] = inference_time
            
            if inference_ok:
                logger.info(f"Ollama fully ready: inference working in {inference_time}ms")
                return True, f"✅ Ready ({inference_time}ms)", details
            else:
                details["error"] = error_msg
                logger.warning(f"Model loaded but inference failed: {error_msg}")
                return False, f"⚠️ Model loaded but not responding: {error_msg[:50]}", details
        else:
            logger.error(f"Ollama API returned status {response.status_code}")
            return False, f"❌ Service error: {response.status_code}", details
            
    except requests.exceptions.Timeout:
        details["response_time_ms"] = int((time.time() - start) * 1000)
        logger.warning(f"Ollama health check timeout after {details['response_time_ms']}ms")
        return False, f"⏱️ Timeout after {details['response_time_ms']}ms (service may be starting)", details
        
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama service")
        return False, "🔌 Cannot connect (service may be starting)", details
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Ollama health check failed: {error_msg}")
        details["error"] = error_msg
        return False, f"❌ {error_msg}", details


def wait_for_ollama_ready(max_wait_seconds: int = 300, check_interval: int = 5) -> Tuple[bool, str]:
    """
    Wait for Ollama service to be ready with timeout
    
    Args:
        max_wait_seconds: Maximum time to wait in seconds (default: 300 = 5 minutes)
        check_interval: Seconds between health checks (default: 5)
        
    Returns:
        Tuple of (is_ready, message)
    """
    start_time = time.time()
    attempt = 0
    
    logger.info(f"Waiting for Ollama to be ready (max {max_wait_seconds}s)...")
    
    while time.time() - start_time < max_wait_seconds:
        attempt += 1
        is_healthy, message, details = check_ollama_health()
        
        elapsed = int(time.time() - start_time)
        
        if is_healthy:
            logger.info(f"Ollama ready after {elapsed}s and {attempt} attempts")
            return True, f"✅ AI service ready (took {elapsed}s)"
        
        # Log progress every 10 attempts
        if attempt % 10 == 0:
            logger.info(f"Attempt {attempt} ({elapsed}s elapsed): {message}")
        
        time.sleep(check_interval)
    
    elapsed = int(time.time() - start_time)
    error_msg = f"❌ AI service not ready after {elapsed}s timeout"
    logger.error(error_msg)
    return False, error_msg


def get_model_info() -> Dict:
    """
    Get detailed information about loaded models
    
    Returns:
        Dictionary with model information or error details
    """
    try:
        response = requests.get(
            f"{Config.OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            return {
                "success": True,
                "model_count": len(models),
                "models": [{
                    "name": m.get('name'),
                    "size_gb": round(m.get('size', 0) / (1024**3), 2),
                    "modified": m.get('modified_at', 'Unknown')
                } for m in models],
                "target_model_loaded": any(m.get('name') == Config.OLLAMA_MODEL_NAME for m in models)
            }
        else:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

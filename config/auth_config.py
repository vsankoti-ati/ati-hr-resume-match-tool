"""
Authentication Configuration Module
Contains Azure AD authentication settings and configuration
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AuthConfig:
    """Azure AD authentication configuration class"""
    
    # Feature flag to enable/disable authentication
    ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'true').lower() == 'true'
    
    # Azure AD Configuration
    AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID', '')
    AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID', '')
    AZURE_AD_CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET', '')
    AZURE_AD_REDIRECT_URI = os.getenv('AZURE_AD_REDIRECT_URI', 'http://localhost:8501')
    
    # Azure AD Authority URL
    AZURE_AD_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}" if AZURE_AD_TENANT_ID else ""
    
    # Scopes - permissions requested from Azure AD
    AZURE_AD_SCOPES = ["User.Read"]
    
    # Token cache settings
    TOKEN_CACHE_FILE = os.getenv('TOKEN_CACHE_FILE', '.token_cache.json')
    
    @staticmethod
    def is_auth_enabled() -> bool:
        """
        Check if authentication is enabled
        
        Returns:
            True if authentication is enabled, False otherwise
        """
        return AuthConfig.ENABLE_AUTH
    
    @staticmethod
    def validate_config() -> tuple[bool, str]:
        """
        Validate Azure AD configuration
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not AuthConfig.is_auth_enabled():
            return True, "Authentication disabled"
        
        errors = []
        
        if not AuthConfig.AZURE_AD_TENANT_ID:
            errors.append("AZURE_AD_TENANT_ID is not set")
        
        if not AuthConfig.AZURE_AD_CLIENT_ID:
            errors.append("AZURE_AD_CLIENT_ID is not set")
        
        if not AuthConfig.AZURE_AD_CLIENT_SECRET:
            errors.append("AZURE_AD_CLIENT_SECRET is not set")
        
        if not AuthConfig.AZURE_AD_REDIRECT_URI:
            errors.append("AZURE_AD_REDIRECT_URI is not set")
        
        if errors:
            return False, f"Authentication configuration errors: {', '.join(errors)}"
        
        return True, "Authentication configuration valid"
    
    @staticmethod
    def get_scopes() -> List[str]:
        """
        Get configured Azure AD scopes
        
        Returns:
            List of scope strings
        """
        return AuthConfig.AZURE_AD_SCOPES.copy()

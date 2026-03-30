"""
Mock Authentication Service Module
Provides fake authentication for local development without Azure AD
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockAuthService:
    """Mock authentication service for development"""
    
    def __init__(self):
        """Initialize mock authentication service"""
        logger.info("Mock authentication service initialized")
    
    def get_auth_url(self, state: str = None) -> str:
        """
        Generate mock authorization URL (not used in mock mode)
        
        Args:
            state: Optional state parameter
            
        Returns:
            Dummy URL string
        """
        return "http://localhost:8501?mock_auth=true"
    
    def acquire_token_by_auth_code(
        self, 
        auth_code: str, 
        redirect_uri: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Mock token acquisition (returns dummy token)
        
        Args:
            auth_code: Authorization code (ignored)
            redirect_uri: Redirect URI (ignored)
            
        Returns:
            Mock token response dictionary
        """
        logger.info("Mock token acquisition")
        
        return {
            "access_token": "mock_access_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "User.Read",
            "id_token": "mock_id_token_12345"
        }
    
    def validate_token(self, access_token: str) -> bool:
        """
        Mock token validation (always returns True)
        
        Args:
            access_token: Access token (ignored)
            
        Returns:
            Always True
        """
        return True
    
    def get_user_info(self, access_token: str = None) -> Dict[str, Any]:
        """
        Get mock user information
        
        Args:
            access_token: Access token (ignored)
            
        Returns:
            Mock user information dictionary
        """
        logger.info("Returning mock user info")
        
        return {
            "email": "dev@example.com",
            "name": "Development User",
            "user_id": "mock-user-id-12345",
            "roles": ["admin"],
            "groups": ["developers"],
            "tenant_id": "mock-tenant-id",
            "token_expiry": datetime.now() + timedelta(hours=24)  # 24 hours from now
        }
    
    def get_token_expiry(self, access_token: str) -> datetime:
        """
        Get mock token expiration (24 hours from now)
        
        Args:
            access_token: Access token (ignored)
            
        Returns:
            Datetime 24 hours in the future
        """
        return datetime.now() + timedelta(hours=24)
    
    def is_token_expired(self, token_expiry: datetime) -> bool:
        """
        Check if token has expired (always False for mock)
        
        Args:
            token_expiry: Token expiration datetime
            
        Returns:
            Always False
        """
        return False
    
    def auto_authenticate(self) -> Dict[str, Any]:
        """
        Automatically authenticate user (for mock mode)
        
        Returns:
            Dictionary containing user info and mock token
        """
        logger.info("Auto-authenticating development user")
        
        user_info = self.get_user_info()
        
        return {
            "authenticated": True,
            "user_email": user_info["email"],
            "user_name": user_info["name"],
            "user_roles": user_info["roles"],
            "user_id": user_info["user_id"],
            "access_token": "mock_access_token_12345",
            "token_expiry": user_info["token_expiry"]
        }


# Create singleton instance
_mock_auth_service = None


def get_mock_auth_service() -> MockAuthService:
    """Get or create singleton mock auth service instance"""
    global _mock_auth_service
    if _mock_auth_service is None:
        _mock_auth_service = MockAuthService()
    return _mock_auth_service

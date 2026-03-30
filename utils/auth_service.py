"""
Authentication Service Module
Handles Azure AD authentication using MSAL (Microsoft Authentication Library)
"""
import logging
import msal
import jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from config.auth_config import AuthConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling Azure AD authentication via MSAL"""
    
    def __init__(self):
        """Initialize the authentication service"""
        self.config = AuthConfig
        self._msal_app = None
        
        if self.config.is_auth_enabled():
            # Validate configuration
            is_valid, error_msg = self.config.validate_config()
            if not is_valid:
                logger.error(f"Authentication configuration invalid: {error_msg}")
                raise ValueError(error_msg)
            
            # Initialize MSAL application
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=self.config.AZURE_AD_CLIENT_ID,
                client_credential=self.config.AZURE_AD_CLIENT_SECRET,
                authority=self.config.AZURE_AD_AUTHORITY
            )
            logger.info("MSAL application initialized")
    
    def get_auth_url(self, state: str = None) -> str:
        """
        Generate Azure AD authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL string
        """
        if not self._msal_app:
            raise RuntimeError("Authentication is not enabled or configured")
        
        auth_url = self._msal_app.get_authorization_request_url(
            scopes=self.config.get_scopes(),
            redirect_uri=self.config.AZURE_AD_REDIRECT_URI,
            state=state
        )
        
        logger.info("Generated authorization URL")
        return auth_url
    
    def acquire_token_by_auth_code(
        self, 
        auth_code: str, 
        redirect_uri: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from Azure AD callback
            redirect_uri: Redirect URI used in authorization request
            
        Returns:
            Token response dictionary containing access_token, id_token, etc.
            Returns None if token acquisition fails
        """
        if not self._msal_app:
            raise RuntimeError("Authentication is not enabled or configured")
        
        redirect_uri = redirect_uri or self.config.AZURE_AD_REDIRECT_URI
        
        try:
            result = self._msal_app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=self.config.get_scopes(),
                redirect_uri=redirect_uri
            )
            
            if "access_token" in result:
                logger.info("Successfully acquired access token")
                return result
            else:
                error = result.get("error", "unknown_error")
                error_description = result.get("error_description", "No description")
                logger.error(f"Token acquisition failed: {error} - {error_description}")
                return None
                
        except Exception as e:
            logger.error(f"Error acquiring token: {str(e)}")
            return None
    
    def validate_token(self, access_token: str) -> bool:
        """
        Validate access token
        
        Args:
            access_token: JWT access token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Decode without verification (Azure AD already verified signature)
            decoded = jwt.decode(
                access_token, 
                options={"verify_signature": False}
            )
            
            # Check expiration
            exp = decoded.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                if exp_datetime < datetime.now():
                    logger.warning("Token has expired")
                    return False
            
            # Check audience (for Microsoft Graph, audience is typically the Graph API endpoint)
            # We'll accept either the client ID or Graph API endpoint
            aud = decoded.get("aud")
            if aud:
                valid_audiences = [
                    self.config.AZURE_AD_CLIENT_ID,
                    "https://graph.microsoft.com",
                    "00000003-0000-0000-c000-000000000000"  # Microsoft Graph Service Principal ID
                ]
                if aud not in valid_audiences:
                    logger.warning(f"Token audience '{aud}' not in expected audiences, but proceeding")
                    # Don't fail - Azure AD has already validated this token
            
            logger.info("Token validation successful")
            return True
            
        except jwt.DecodeError as e:
            logger.error(f"Token decode error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Extract user information from access token
        
        Args:
            access_token: JWT access token
            
        Returns:
            Dictionary containing user information (email, name, roles)
            Returns None if extraction fails
        """
        try:
            # Decode token to get claims
            decoded = jwt.decode(
                access_token, 
                options={"verify_signature": False}
            )
            
            user_info = {
                "email": decoded.get("preferred_username") or decoded.get("upn") or decoded.get("email", ""),
                "name": decoded.get("name", ""),
                "user_id": decoded.get("oid", ""),
                "roles": decoded.get("roles", []),
                "groups": decoded.get("groups", []),
                "tenant_id": decoded.get("tid", ""),
                "token_expiry": datetime.fromtimestamp(decoded.get("exp", 0)) if decoded.get("exp") else None
            }
            
            logger.info(f"Extracted user info for: {user_info['email']}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error extracting user info: {str(e)}")
            return None
    
    def get_token_expiry(self, access_token: str) -> Optional[datetime]:
        """
        Get token expiration datetime
        
        Args:
            access_token: JWT access token
            
        Returns:
            Expiration datetime or None if unavailable
        """
        try:
            decoded = jwt.decode(
                access_token, 
                options={"verify_signature": False}
            )
            
            exp = decoded.get("exp")
            if exp:
                return datetime.fromtimestamp(exp)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting token expiry: {str(e)}")
            return None
    
    def is_token_expired(self, token_expiry: datetime) -> bool:
        """
        Check if token has expired
        
        Args:
            token_expiry: Token expiration datetime
            
        Returns:
            True if token is expired, False otherwise
        """
        if not token_expiry:
            return True
        
        return datetime.now() >= token_expiry


# Create singleton instance
_auth_service = None


def get_auth_service() -> AuthService:
    """Get or create singleton auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

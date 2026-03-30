"""
Authentication Wrapper Module
Provides authentication decorator and utilities for protecting Streamlit pages
"""
import streamlit as st
import logging
from datetime import datetime
from typing import Callable
from config.auth_config import AuthConfig
from utils.auth_service import get_auth_service
from utils.mock_auth import get_mock_auth_service
from app.login import render_login_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def require_authentication() -> bool:
    """
    Check if user is authenticated and redirect to login if not
    
    Returns:
        True if user is authenticated, False otherwise
    """
    
    # If authentication is disabled, auto-authenticate with mock service
    if not AuthConfig.is_auth_enabled():
        if not st.session_state.get('authenticated', False):
            logger.info("Authentication disabled - performing mock authentication")
            mock_service = get_mock_auth_service()
            auth_data = mock_service.auto_authenticate()
            
            # Store authentication data in session state
            for key, value in auth_data.items():
                st.session_state[key] = value
        
        return True
    
    # Check if user is authenticated
    is_authenticated = st.session_state.get('authenticated', False)
    
    if not is_authenticated:
        # User not authenticated - show login page
        logger.info("User not authenticated - displaying login page")
        render_login_page()
        st.stop()  # Stop execution to prevent rendering main app
        return False
    
    # Check if token has expired
    token_expiry = st.session_state.get('token_expiry')
    if token_expiry:
        auth_service = get_auth_service()
        if auth_service.is_token_expired(token_expiry):
            logger.warning("Token has expired - requiring re-authentication")
            logout()
            st.warning("Your session has expired. Please sign in again.")
            render_login_page()
            st.stop()
            return False
    
    logger.info(f"User authenticated: {st.session_state.get('user_email', 'unknown')}")
    return True


def logout():
    """Clear authentication session and logout user"""
    
    logger.info(f"Logging out user: {st.session_state.get('user_email', 'unknown')}")
    
    # Clear all authentication-related session state
    auth_keys = [
        'authenticated',
        'user_email',
        'user_name',
        'user_id',
        'user_roles',
        'access_token',
        'token_expiry',
        'auth_state',
        'last_processed_auth_code'
    ]
    
    for key in auth_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    logger.info("User logged out successfully")


def display_logout_button():
    """Display logout button in sidebar"""
    
    is_authenticated = st.session_state.get('authenticated', False)
    
    if is_authenticated:
        user_name = st.session_state.get('user_name', 'User')
        user_email = st.session_state.get('user_email', '')
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Signed In")
        st.sidebar.markdown(f"**{user_name}**")
        st.sidebar.markdown(f"*{user_email}*")
        
        if st.sidebar.button("🚪 Sign Out", use_container_width=True):
            logout()
            # Clear query params to ensure clean state
            st.query_params.clear()
            st.rerun()


def check_user_role(required_role: str) -> bool:
    """
    Check if authenticated user has a specific role
    
    Args:
        required_role: Role name to check
        
    Returns:
        True if user has the role, False otherwise
    """
    
    user_roles = st.session_state.get('user_roles', [])
    
    has_role = required_role in user_roles
    
    if not has_role:
        logger.warning(f"User does not have required role: {required_role}")
    
    return has_role


def require_role(required_role: str):
    """
    Require user to have a specific role, show error if not
    
    Args:
        required_role: Role name to require
    """
    
    if not check_user_role(required_role):
        st.error(f"⚠️ Access Denied: This feature requires the '{required_role}' role.")
        st.info("Please contact your administrator if you believe you should have access.")
        st.stop()


def get_current_user() -> dict:
    """
    Get current authenticated user information
    
    Returns:
        Dictionary containing user information
    """
    
    return {
        "email": st.session_state.get('user_email', ''),
        "name": st.session_state.get('user_name', ''),
        "user_id": st.session_state.get('user_id', ''),
        "roles": st.session_state.get('user_roles', []),
        "is_authenticated": st.session_state.get('authenticated', False)
    }

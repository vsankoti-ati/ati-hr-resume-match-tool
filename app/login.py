"""
Login Page Component
Handles Azure AD authentication UI for Streamlit
"""
import streamlit as st
import logging
from typing import Optional
import secrets
from config.auth_config import AuthConfig
from utils.auth_service import get_auth_service
from utils.mock_auth import get_mock_auth_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def render_login_page():
    """Render the Azure AD login page"""
    
    # Check if authentication is enabled
    if not AuthConfig.is_auth_enabled():
        # Auto-authenticate with mock service
        with st.spinner("🔄 Initializing session..."):
            logger.info("Authentication disabled - using mock authentication")
            mock_service = get_mock_auth_service()
            auth_data = mock_service.auto_authenticate()
            
            # Store authentication data in session state
            for key, value in auth_data.items():
                st.session_state[key] = value
        
        st.rerun()
        return
    
    # Display login page header
    st.markdown("""
    <style>
        .login-container {
            max-width: 500px;
            margin: 100px auto;
            padding: 40px;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            color: #1f497d;
            margin-bottom: 30px;
        }
        .login-button {
            display: flex;
            justify-content: center;
            margin-top: 30px;
        }
        .info-text {
            text-align: center;
            color: #6c757d;
            margin-top: 20px;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-header">📄 HR Resume Match Tool</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #6c757d;">Sign In Required</h3>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Check for authentication callback
    query_params = st.query_params
    
    if "code" in query_params:
        # Handle OAuth callback from Microsoft
        handle_auth_callback(query_params)
    else:
        # Show login button
        display_login_button()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display info text
    st.markdown(
        '<p class="info-text">This application uses Azure Active Directory for authentication.<br>'
        'Please sign in with your organizational account.</p>',
        unsafe_allow_html=True
    )


def display_login_button():
    """Display the Azure AD login button"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔐 Sign in with Microsoft", type="primary", use_container_width=True):
            try:
                with st.spinner("🔄 Preparing authentication..."):
                    # Generate state parameter for CSRF protection
                    state = secrets.token_urlsafe(32)
                    st.session_state.auth_state = state
                    
                    # Get authorization URL
                    auth_service = get_auth_service()
                    auth_url = auth_service.get_auth_url(state=state)
                    
                    logger.info("Redirecting to Azure AD login")
                
                # Display redirect message
                st.info("✅ Redirecting to Microsoft login page...")
                
                # Redirect to Azure AD
                st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Authentication error: {str(e)}")
                logger.error(f"Error generating auth URL: {str(e)}")


def handle_auth_callback(query_params: dict):
    """
    Handle the OAuth2 callback from Azure AD
    
    Args:
        query_params: Query parameters from the callback URL
    """
    
    try:
        # Extract authorization code and state
        auth_code = query_params.get("code")
        state = query_params.get("state")
        
        # Handle state and code as list (Streamlit query_params can return lists)
        if isinstance(auth_code, list):
            auth_code = auth_code[0]
        if isinstance(state, list):
            state = state[0]
        
        # Check if we've already processed this code to prevent reuse
        last_processed_code = st.session_state.get("last_processed_auth_code")
        if last_processed_code == auth_code:
            logger.warning("Attempting to reuse authorization code - clearing and showing login")
            st.query_params.clear()
            if "last_processed_auth_code" in st.session_state:
                del st.session_state["last_processed_auth_code"]
            st.error("Session expired. Please sign in again.")
            st.rerun()
            return
        
        if not auth_code:
            st.error("Authorization code not received. Please try again.")
            st.query_params.clear()
            return
        
        # Exchange authorization code for access token
        with st.spinner("🔄 Exchanging authorization code..."):
            auth_service = get_auth_service()
            token_response = auth_service.acquire_token_by_auth_code(
                auth_code=auth_code
            )
        
        if not token_response or "access_token" not in token_response:
            st.error("Failed to acquire access token. Please try again.")
            logger.error(f"Token acquisition failed. Response: {token_response}")
            # Clear the bad code from URL
            st.query_params.clear()
            if st.button("Try Again"):
                st.rerun()
            return
        
        # Extract access token
        access_token = token_response["access_token"]
        
        # Validate token
        with st.spinner("🔐 Validating access token..."):
            if not auth_service.validate_token(access_token):
                st.error("Token validation failed. Please try again.")
                logger.error("Token validation failed")
                return
        
        # Get user information
        with st.spinner("👤 Retrieving user information..."):
            user_info = auth_service.get_user_info(access_token)
        
        if not user_info:
            st.error("Failed to retrieve user information. Please try again.")
            logger.error("User info extraction failed")
            return
        
        # Store authentication data in session state
        st.session_state.authenticated = True
        st.session_state.user_email = user_info["email"]
        st.session_state.user_name = user_info["name"]
        st.session_state.user_id = user_info["user_id"]
        st.session_state.user_roles = user_info["roles"]
        st.session_state.access_token = access_token
        st.session_state.token_expiry = user_info["token_expiry"]
        
        # Store this code as processed to prevent reuse
        st.session_state.last_processed_auth_code = auth_code
        
        # Clear auth state
        if "auth_state" in st.session_state:
            del st.session_state.auth_state
        
        logger.info(f"User authenticated successfully: {user_info['email']}")
        
        # Clear query parameters and redirect to main app
        st.query_params.clear()
        st.success("✅ Sign in successful! Redirecting...")
        st.rerun()
        
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        logger.error(f"Error handling auth callback: {str(e)}")


def display_user_profile(user_name: str, user_email: str):
    """
    Display user profile information
    
    Args:
        user_name: User's display name
        user_email: User's email address
    """
    
    st.markdown("---")
    st.markdown("### 👤 Signed In As")
    st.markdown(f"**Name:** {user_name}")
    st.markdown(f"**Email:** {user_email}")

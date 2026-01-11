# Thanks mkhorasani for his authentication package that I used to build this
# https://github.com/mkhorasani/Streamlit-Authenticator

import os
import time
import streamlit as st
from typing import Literal, Optional, Dict, Any
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json
from streamlit_auth_cookie import CookieHandler


class Authenticate:
    def __init__(self, 
                 secret_credentials_path: str, 
                 redirect_uri: str, 
                 cookie_name: str, 
                 cookie_key: str,
                 cookie_expiry_days: float = 30.0):
        """
        Initialize the Authenticate class for Google OAuth2 authentication.
        
        Args:
            secret_credentials_path: Path to Google OAuth2 credentials JSON file
            redirect_uri: The redirect URI registered with Google OAuth2
            cookie_name: Name of the authentication cookie
            cookie_key: Secret key for cookie encryption
            cookie_expiry_days: Number of days before cookie expires
        """
        # Initialize session state variables
        if 'connected' not in st.session_state:
            st.session_state['connected'] = False
        if 'user_info' not in st.session_state:
            st.session_state['user_info'] = None
        if 'oauth_id' not in st.session_state:
            st.session_state['oauth_id'] = None
        if 'credentials' not in st.session_state:
            st.session_state['credentials'] = None
        if 'oauth_state' not in st.session_state:
            st.session_state['oauth_state'] = None
        
        self.secret_credentials_path = secret_credentials_path
        self.redirect_uri = redirect_uri
        self.cookie_handler = CookieHandler(cookie_name,
                                            cookie_key,
                                            cookie_expiry_days)
        
        # Validate credentials file exists
        if not os.path.exists(secret_credentials_path):
            st.error(f"Credentials file not found: {secret_credentials_path}")
            raise FileNotFoundError(f"Credentials file not found: {secret_credentials_path}")

    def get_authorization_url(self) -> str:
        """
        Generate the Google OAuth2 authorization URL.
        
        Returns:
            Authorization URL for Google OAuth2
        """
        try:
            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                self.secret_credentials_path,
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
                redirect_uri=self.redirect_uri,
            )

            authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent"
            )

            st.session_state['oauth_state'] = state
            return authorization_url
            
        except Exception as e:
            st.error(f"Error generating authorization URL: {str(e)}")
            raise

    def login(self, 
              color: Literal['white', 'blue'] = 'blue', 
              justify_content: str = "center", 
              sidebar: bool = False) -> None:
        """
        Display Google login button.
        
        Args:
            color: Button color theme ('white' or 'blue')
            justify_content: CSS justify-content value for button alignment
            sidebar: Whether to display in sidebar
        """
        if not st.session_state.get('connected', False):
            try:
                authorization_url = self.get_authorization_url()
                
                html_content = f"""
<div style="display: flex; justify-content: {justify_content};">
    <a href="{authorization_url}" target="_self" style="background-color: {'#fff' if color == 'white' else '#4285f4'}; color: {'#000' if color == 'white' else '#fff'}; text-decoration: none; text-align: center; font-size: 16px; margin: 4px 2px; cursor: pointer; padding: 8px 12px; border-radius: 4px; display: flex; align-items: center; border: 1px solid {'#dadce0' if color == 'white' else '#4285f4'};">
        <img src="https://lh3.googleusercontent.com/COxitqgJr1sJnIDe8-jiKhxDx1FrYbtRHKJ9z_hELisAlapwE9LUPh6fcXIfb5vwpbMl4xl9H9TRFPc5NOO8Sb3VSgIBrfRYvW6cUA" alt="Google logo" style="margin-right: 8px; width: 26px; height: 26px; background-color: white; border: 2px solid white; border-radius: 4px;">
        Sign in with Google
    </a>
</div>
"""
                if sidebar:
                    st.sidebar.markdown(html_content, unsafe_allow_html=True)
                else:
                    st.markdown(html_content, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error displaying login button: {str(e)}")

    def check_authentification(self) -> bool:
        """
        Check if user is authenticated via cookie or OAuth callback.
        
        Returns:
            True if user is authenticated, False otherwise
        """
        # First, check if already authenticated in session state
        if st.session_state.get('connected', False):
            return True

        # Check for authentication cookie
        token = self.cookie_handler.get_cookie()
        if token:
            try:
                user_info = {
                    'name': token.get('name'),
                    'email': token.get('email'),
                    'picture': token.get('picture'),
                    'id': token.get('oauth_id')
                }
                
                # Validate required user info
                if not all([user_info['name'], user_info['email'], user_info['id']]):
                    st.warning("Invalid authentication cookie")
                    self.cookie_handler.delete_cookie()
                    return False
                
                st.session_state["connected"] = True
                st.session_state["user_info"] = user_info
                st.session_state["oauth_id"] = user_info.get("id")
                
                # Clear query parameters
                if st.query_params.get("code"):
                    st.query_params.clear()
                    
                return True
                
            except Exception as e:
                st.error(f"Error processing authentication cookie: {str(e)}")
                self.cookie_handler.delete_cookie()
                return False

        # Check for OAuth callback
        auth_code = st.query_params.get("code")
        if auth_code:
            try:
                flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                    self.secret_credentials_path,
                    scopes=[
                        "openid",
                        "https://www.googleapis.com/auth/userinfo.profile",
                        "https://www.googleapis.com/auth/userinfo.email",
                        "https://www.googleapis.com/auth/gmail.readonly",
                        "https://www.googleapis.com/auth/gmail.send",
                    ],
                    redirect_uri=self.redirect_uri,
                )
                
                # Fetch token using authorization code
                flow.fetch_token(code=auth_code)
                credentials = flow.credentials
                
                # Store credentials in session state
                st.session_state["credentials"] = credentials.to_json()
                
                # Get user info
                user_info_service = build(
                    serviceName="oauth2",
                    version="v2",
                    credentials=credentials,
                )
                user_info = user_info_service.userinfo().get().execute()
                
                # Set session state
                st.session_state["connected"] = True
                st.session_state["oauth_id"] = user_info.get("id")
                st.session_state["user_info"] = user_info
                
                # Set cookie
                self.cookie_handler.set_cookie(
                    user_info.get("name"),
                    user_info.get("email"),
                    user_info.get("picture"),
                    user_info.get("id")
                )
                
                # Clear query parameters and rerun
                st.query_params.clear()
                st.rerun()
                
                return True
                
            except Exception as e:
                st.error(f"Error during OAuth callback: {str(e)}")
                return False
        
        return False

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get authenticated user information.
        
        Returns:
            Dictionary with user info or None if not authenticated
        """
        if st.session_state.get('connected', False):
            return st.session_state.get('user_info')
        return None

    def get_credentials(self) -> Optional[Credentials]:
        """
        Get Google OAuth2 credentials for API calls.
        
        Returns:
            Credentials object or None if not available
        """
        if st.session_state.get('connected', False) and st.session_state.get('credentials'):
            try:
                credentials_info = json.loads(st.session_state["credentials"])
                return Credentials.from_authorized_user_info(credentials_info)
            except Exception as e:
                st.error(f"Error loading credentials: {str(e)}")
                return None
        return None

    def logout(self) -> None:
        """
        Logout the current user and clear all session data.
        """
        # Clear cookie
        self.cookie_handler.delete_cookie()
        
        # Clear session state
        st.session_state.clear()
        
        # Reinitialize default session state
        st.session_state['connected'] = False
        st.session_state['user_info'] = None
        st.session_state['oauth_id'] = None
        st.session_state['credentials'] = None
        st.session_state['oauth_state'] = None
        
        st.rerun()

    def get_authenticated_user_email(self) -> Optional[str]:
        """
        Get the email of the authenticated user.
        
        Returns:
            Email address or None if not authenticated
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('email')
        return None

    def get_authenticated_user_name(self) -> Optional[str]:
        """
        Get the name of the authenticated user.
        
        Returns:
            User's name or None if not authenticated
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('name')
        return None

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return st.session_state.get('connected', False)

    def display_user_info(self, sidebar: bool = False) -> None:
        """
        Display user information and logout button.
        
        Args:
            sidebar: Whether to display in sidebar
        """
        if self.is_authenticated():
            user_info = self.get_user_info()
            if user_info:
                container = st.sidebar if sidebar else st
                
                with container:
                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if user_info.get('picture'):
                            st.image(user_info['picture'], width=40)
                    with col2:
                        st.write(f"**{user_info.get('name', 'User')}**")
                        st.write(user_info.get('email', ''))
                    
                    if st.button("Logout", key="logout_button"):
                        self.logout()

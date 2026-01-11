from datetime import datetime, timedelta
import jwt
from jwt import DecodeError, InvalidSignatureError, ExpiredSignatureError
import streamlit as st
import extra_streamlit_components as stx
from typing import Optional, Dict, Any, Union
import logging

# Set up logging
logger = logging.getLogger(__name__)


class CookieHandler:
    def __init__(self, cookie_name: str, cookie_key: str, cookie_expiry_days: float = 30.0):
        """
        Create a new instance of "CookieHandler" for managing authentication cookies.

        Parameters
        ----------
        cookie_name: str
            Name of the cookie stored on the client's browser for password-less re-authentication.
        cookie_key: str
            Key to be used to hash the signature of the re-authentication cookie.
        cookie_expiry_days: float
            Number of days before the re-authentication cookie automatically expires on the client's
            browser.
        """
        self.cookie_name = cookie_name
        self.cookie_key = cookie_key
        self.cookie_expiry_days = cookie_expiry_days
        self.cookie_manager = self._initialize_cookie_manager()
        self.token = None
        self.exp_date = None

    def _initialize_cookie_manager(self) -> stx.CookieManager:
        """
        Initialize and return the CookieManager instance.
        
        Returns
        -------
        CookieManager
            Initialized cookie manager instance.
        
        Raises
        ------
        RuntimeError
            If cookie manager fails to initialize.
        """
        try:
            # Initialize cookie manager with better error handling
            cookie_manager = stx.CookieManager()
            
            # Test if cookie manager is working
            cookies = cookie_manager.get_all()
            if cookies is None:
                # Cookie manager might need time to initialize
                logger.info("Cookie manager initialized, waiting for browser cookies...")
            
            return cookie_manager
            
        except Exception as e:
            logger.error(f"Failed to initialize CookieManager: {str(e)}")
            raise RuntimeError(f"CookieManager initialization failed: {str(e)}")

    def get_cookie(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves, validates, and returns the re-authentication cookie.

        Returns
        -------
        Dict[str, Any] or None
            Decoded cookie data if valid, None otherwise.
        """
        try:
            # Check if logout is in progress
            if st.session_state.get('logout', False):
                logger.info("Logout in progress, skipping cookie retrieval")
                return None

            # Get cookie from manager
            cookie_value = self.cookie_manager.get(self.cookie_name)
            
            if cookie_value is None:
                logger.debug("No authentication cookie found")
                return None

            # Decode and validate the token
            decoded_token = self._token_decode(cookie_value)
            
            if decoded_token and self._validate_token(decoded_token):
                logger.debug(f"Valid authentication cookie found for user: {decoded_token.get('email')}")
                return decoded_token
            else:
                # If token is invalid, clean it up
                self.delete_cookie()
                return None

        except Exception as e:
            logger.error(f"Error retrieving cookie: {str(e)}")
            return None

    def _validate_token(self, token: Dict[str, Any]) -> bool:
        """
        Validate the decoded JWT token.

        Parameters
        ----------
        token: Dict[str, Any]
            Decoded JWT token

        Returns
        -------
        bool
            True if token is valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['email', 'name', 'oauth_id', 'exp_date']
            for field in required_fields:
                if field not in token:
                    logger.warning(f"Missing required field in token: {field}")
                    return False

            # Check expiration
            exp_timestamp = token.get('exp_date')
            if not isinstance(exp_timestamp, (int, float)):
                logger.warning("Invalid expiration date format")
                return False

            current_timestamp = datetime.now().timestamp()
            if exp_timestamp <= current_timestamp:
                logger.info("Token has expired")
                return False

            return True

        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False

    def delete_cookie(self) -> bool:
        """
        Deletes the re-authentication cookie.

        Returns
        -------
        bool
            True if cookie was deleted successfully, False otherwise.
        """
        try:
            self.cookie_manager.delete(self.cookie_name)
            logger.info("Authentication cookie deleted successfully")
            return True
            
        except KeyError as e:
            logger.warning(f"Cookie not found for deletion: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deleting cookie: {str(e)}")
            return False

    def set_cookie(self, name: str, email: str, picture: str, oauth_id: str) -> bool:
        """
        Sets the re-authentication cookie.

        Parameters
        ----------
        name: str
            User's full name
        email: str
            User's email address
        picture: str
            URL to user's profile picture
        oauth_id: str
            User's OAuth ID

        Returns
        -------
        bool
            True if cookie was set successfully, False otherwise.
        """
        try:
            # Validate inputs
            if not all([name, email, oauth_id]):
                logger.error("Missing required user information for cookie")
                return False

            # Set expiration date
            self.exp_date = self._set_exp_date()
            
            # Create and encode token
            token = self._token_encode(name, email, picture, oauth_id)
            
            if not token:
                logger.error("Failed to encode authentication token")
                return False

            # Set cookie with expiration
            expires_at = datetime.now() + timedelta(days=self.cookie_expiry_days)
            self.cookie_manager.set(
                self.cookie_name,
                token,
                expires_at=expires_at
            )
            
            logger.info(f"Authentication cookie set for user: {email}")
            return True

        except Exception as e:
            logger.error(f"Error setting cookie: {str(e)}")
            return False

    def _set_exp_date(self) -> float:
        """
        Sets the re-authentication cookie's expiry date.

        Returns
        -------
        float
            re-authentication cookie's expiry timestamp in Unix Epoch.
        """
        return (datetime.now() + timedelta(days=self.cookie_expiry_days)).timestamp()

    def _token_decode(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes the contents of the re-authentication cookie.

        Parameters
        ----------
        token: str
            JWT token string

        Returns
        -------
        Dict[str, Any] or None
            Decoded token dictionary or None if decoding fails.
        """
        try:
            # Decode the JWT token
            decoded = jwt.decode(
                token,
                self.cookie_key,
                algorithms=['HS256'],
                options={'verify_exp': False}  # We'll validate expiration separately
            )
            return decoded
            
        except InvalidSignatureError as e:
            logger.warning(f"Invalid token signature: {str(e)}")
            return None
        except DecodeError as e:
            logger.warning(f"Token decode error: {str(e)}")
            return None
        except ExpiredSignatureError as e:
            logger.info(f"Token has expired: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected token decode error: {str(e)}")
            return None

    def _token_encode(self, name: str, email: str, picture: str, oauth_id: str) -> Optional[str]:
        """
        Encodes the contents of the re-authentication cookie.

        Parameters
        ----------
        name: str
            User's full name
        email: str
            User's email address
        picture: str
            URL to user's profile picture
        oauth_id: str
            User's OAuth ID

        Returns
        -------
        str or None
            Encoded JWT token or None if encoding fails.
        """
        try:
            payload = {
                'email': email,
                'name': name,
                'picture': picture,
                'oauth_id': oauth_id,
                'exp_date': self.exp_date,
                'iat': datetime.now().timestamp(),  # Issued at timestamp
                'iss': 'streamlit_auth'  # Issuer
            }
            
            # Remove None values from payload
            payload = {k: v for k, v in payload.items() if v is not None}
            
            token = jwt.encode(
                payload,
                self.cookie_key,
                algorithm='HS256'
            )
            
            # Ensure token is string (PyJWT returns bytes in some versions)
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            return token
            
        except Exception as e:
            logger.error(f"Error encoding token: {str(e)}")
            return None

    def refresh_cookie(self, name: str = None, email: str = None, 
                      picture: str = None, oauth_id: str = None) -> bool:
        """
        Refresh the authentication cookie with current user data or new data.

        Parameters
        ----------
        name: str, optional
            New name (uses existing if None)
        email: str, optional
            New email (uses existing if None)
        picture: str, optional
            New picture (uses existing if None)
        oauth_id: str, optional
            New OAuth ID (uses existing if None)

        Returns
        -------
        bool
            True if cookie was refreshed successfully, False otherwise.
        """
        try:
            # Get current cookie data
            current_data = self.get_cookie()
            
            if not current_data:
                logger.warning("No existing cookie to refresh")
                return False

            # Use provided values or existing values
            refresh_name = name if name is not None else current_data.get('name')
            refresh_email = email if email is not None else current_data.get('email')
            refresh_picture = picture if picture is not None else current_data.get('picture')
            refresh_oauth_id = oauth_id if oauth_id is not None else current_data.get('oauth_id')

            # Set new cookie
            return self.set_cookie(refresh_name, refresh_email, refresh_picture, refresh_oauth_id)

        except Exception as e:
            logger.error(f"Error refreshing cookie: {str(e)}")
            return False

    def get_cookie_expiry(self) -> Optional[datetime]:
        """
        Get the expiration datetime of the current cookie.

        Returns
        -------
        datetime or None
            Expiration datetime if cookie exists, None otherwise.
        """
        cookie_data = self.get_cookie()
        if cookie_data and 'exp_date' in cookie_data:
            try:
                return datetime.fromtimestamp(cookie_data['exp_date'])
            except (ValueError, TypeError):
                return None
        return None

    def is_cookie_valid(self) -> bool:
        """
        Check if a valid authentication cookie exists.

        Returns
        -------
        bool
            True if valid cookie exists, False otherwise.
        """
        return self.get_cookie() is not None

    def clear_all_cookies(self) -> bool:
        """
        Clear all cookies managed by this handler.

        Returns
        -------
        bool
            True if all cookies were cleared successfully, False otherwise.
        """
        try:
            # Get all cookies
            all_cookies = self.cookie_manager.get_all()
            
            if all_cookies:
                for cookie_name in all_cookies.keys():
                    try:
                        self.cookie_manager.delete(cookie_name)
                    except Exception:
                        continue
                        
            logger.info("All cookies cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all cookies: {str(e)}")
            return False

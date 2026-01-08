"""
Authentication utilities for BotForm2.

Handles password hashing, token generation, and session management.
"""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
import secrets

from ..config import config


# In-memory session storage (for simple implementation)
# In production, use Redis or database
active_sessions = {}
failed_login_attempts = {}


class AuthManager:
    """Manages authentication and sessions."""

    def __init__(self, _secret_key=None):
        """
        Initialize auth manager.

        Args:
            _secret_key: Secret key for JWT tokens
        """
        self.secret_key = _secret_key if _secret_key is not None else config.secret_key
        self.algorithm = "HS256"
        self.session_timeout = config.session_timeout

    def hash_password(self, _password):
        """
        Hash a password.

        Args:
            _password: Plain text password

        Returns:
            Hashed password
        """
        return bcrypt.hashpw(_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, _plain_password, _hashed_password):
        """
        Verify a password against a hash.

        Args:
            _plain_password: Plain text password
            _hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(_plain_password.encode('utf-8'), _hashed_password.encode('utf-8'))
        except Exception:
            return False

    def create_session_token(self, _username, _role='guest'):
        """
        Create a new session token.

        Args:
            _username: Username for the session
            _role: User role (admin or guest)

        Returns:
            Session token string
        """
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=self.session_timeout)

        active_sessions[session_id] = {
            'username': _username,
            'role': _role,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'ip_address': None
        }

        return session_id

    def validate_session(self, _session_token):
        """
        Validate a session token.

        Args:
            _session_token: Session token to validate

        Returns:
            Username if validated, None otherwise
        """
        if _session_token is None:
            return None

        session = active_sessions.get(_session_token)

        if session is None:
            return None

        # Check if session expired
        if datetime.utcnow() > session['expires_at']:
            del active_sessions[_session_token]
            return None

        # Extend session on activity
        session['expires_at'] = datetime.utcnow() + timedelta(seconds=self.session_timeout)

        return session['username']

    def invalidate_session(self, _session_token):
        """
        Invalidate a session token.

        Args:
            _session_token: Session token to invalidate
        """
        if _session_token in active_sessions:
            del active_sessions[_session_token]

    def check_brute_force(self, _username):
        """
        Check if username has too many failed login attempts.

        Args:
            _username: Username to check

        Returns:
            True if allowed to attempt login, False if locked out
        """
        attempts_data = failed_login_attempts.get(_username)

        if attempts_data is None:
            return True

        # Check if lockout period expired
        lockout_until = attempts_data.get('lockout_until')
        if lockout_until is not None:
            if datetime.utcnow() > lockout_until:
                # Lockout expired, reset
                del failed_login_attempts[_username]
                return True
            else:
                return False

        return True

    def record_failed_login(self, _username):
        """
        Record a failed login attempt.

        Args:
            _username: Username that failed login
        """
        if _username not in failed_login_attempts:
            failed_login_attempts[_username] = {
                'count': 0,
                'last_attempt': None,
                'lockout_until': None
            }

        attempts_data = failed_login_attempts[_username]
        attempts_data['count'] = attempts_data['count'] + 1
        attempts_data['last_attempt'] = datetime.utcnow()

        # Lock out after MAX_LOGIN_ATTEMPTS
        if attempts_data['count'] >= config.max_login_attempts:
            attempts_data['lockout_until'] = datetime.utcnow() + timedelta(seconds=config.login_timeout)

    def record_successful_login(self, _username):
        """
        Record a successful login (clears failed attempts).

        Args:
            _username: Username that successfully logged in
        """
        if _username in failed_login_attempts:
            del failed_login_attempts[_username]

    def get_session_from_request(self, _request):
        """
        Extract session token from request cookies.

        Args:
            _request: FastAPI request object

        Returns:
            Session token if found, None otherwise
        """
        return _request.cookies.get('session_token')

    def get_user_info(self, _session_token):
        """
        Get user info from session token.

        Args:
            _session_token: Session token

        Returns:
            Dict with username and role, or None if invalid
        """
        if _session_token is None:
            return None

        session = active_sessions.get(_session_token)

        if session is None:
            return None

        # Check if session expired
        if datetime.utcnow() > session['expires_at']:
            del active_sessions[_session_token]
            return None

        return {
            'username': session['username'],
            'role': session.get('role', 'guest')
        }

    def is_admin(self, _session_token):
        """
        Check if user is admin.

        Args:
            _session_token: Session token

        Returns:
            True if admin, False otherwise
        """
        user_info = self.get_user_info(_session_token)
        if user_info is None:
            return False
        return True if user_info.get('role') == 'admin' else False

    def require_auth(self, _request):
        """
        Require authentication for a request.

        Args:
            _request: FastAPI request object

        Returns:
            Username if authenticated

        Raises:
            HTTPException if not authenticated
        """
        session_token = self.get_session_from_request(_request)
        username = self.validate_session(session_token)

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        return username


# Global auth manager instance
auth_manager = AuthManager()


def get_current_user(_request):
    """
    Dependency to get current user from request.

    Args:
        _request: FastAPI request object

    Returns:
        Username if authenticated, None otherwise
    """
    session_token = _request.cookies.get('session_token')
    if session_token is None:
        return None
    return auth_manager.validate_session(session_token)

"""
Authentication routes for BotForm2.

Handles login, logout, and session management.
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ..utils.auth import auth_manager


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str


@router.post("/login")
async def login(_request: Request, _response: Response, _login_data: LoginRequest):
    """
    Handle user login.

    Args:
        _request: FastAPI request object
        _response: FastAPI response object
        _login_data: Login credentials

    Returns:
        Login response with session cookie
    """
    username = _login_data.username
    password = _login_data.password

    # Check if user is locked out
    if auth_manager.check_brute_force(username) == False:
        lockout_data = auth_manager.failed_login_attempts.get(username)
        lockout_until = lockout_data.get('lockout_until')

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'error': 'Too many failed login attempts',
                'lockout_until': lockout_until.isoformat()
            }
        )

    # Get database manager
    db_manager = _request.app.state.db_manager

    # Look up user in database
    user = await db_manager.get_user_by_username(username)

    if user is None:
        auth_manager.record_failed_login(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials'
        )

    # Verify password
    stored_hash = user['password_hash']
    if auth_manager.verify_password(password, stored_hash) == False:
        auth_manager.record_failed_login(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials'
        )

    # Successful login
    auth_manager.record_successful_login(username)

    # Get user role
    user_role = user['role']

    # Create session with role
    session_token = auth_manager.create_session_token(username, user_role)

    # Set cookie
    _response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        max_age=auth_manager.session_timeout,
        samesite='lax'
    )

    logger.info("User {} logged in successfully with role {}".format(username, user_role))

    return {
        'success': True,
        'message': 'Login successful',
        'username': username,
        'role': user_role
    }


@router.post("/logout")
async def logout(_request: Request, _response: Response):
    """
    Handle user logout.

    Args:
        _request: FastAPI request object
        _response: FastAPI response object

    Returns:
        Logout confirmation
    """
    session_token = auth_manager.get_session_from_request(_request)

    if session_token is not None:
        auth_manager.invalidate_session(session_token)

    # Clear cookie
    _response.delete_cookie(key='session_token')

    return {
        'success': True,
        'message': 'Logout successful'
    }


@router.get("/session")
async def check_session(_request: Request):
    """
    Check if user has active session.

    Args:
        _request: FastAPI request object

    Returns:
        Session status
    """
    session_token = auth_manager.get_session_from_request(_request)
    username = auth_manager.validate_session(session_token)

    if username is not None:
        return {
            'authenticated': True,
            'username': username
        }
    else:
        return {
            'authenticated': False
        }

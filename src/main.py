"""
FastAPI application entry point for BotForm2.

Main web server and API implementation.
"""

import logging
import asyncio
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import config
from .database.manager import DatabaseManager
from .api.polymarket import PolymarketClient
from .bots.bot_manager import BotManager
from .utils.vpn_check import VPNChecker
from .utils.auth import auth_manager, get_current_user
from .api import routes
from .api import auth_routes

# Configure logging
logging.basicConfig(
    level=config.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global instances
db_manager = None
polymarket_client = None
bot_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    global db_manager, polymarket_client, bot_manager

    logger.info("Starting BotForm2 application")

    # VPN check
    if config.require_vpn == True:
        logger.info("Performing VPN check")
        vpn_checker = VPNChecker(
            _allowed_ips=config.allowed_vpn_ips,
            _required=True
        )
        try:
            await vpn_checker.validate_or_exit()
        except SystemExit:
            logger.critical("VPN check failed, exiting")
            raise

    # Initialize database
    logger.info("Initializing database")
    db_manager = DatabaseManager.get_instance(_connection_string=config.database_url)
    try:
        await db_manager.initialize()
    except Exception as e:
        logger.error("Database initialization failed: {}".format(str(e)))
        logger.warning("Continuing without database (will fail on first DB operation)")

    # Initialize Polymarket client
    logger.info("Initializing Polymarket client")
    polymarket_client = PolymarketClient(
        _api_key=config.polymarket_api_key,
        _api_secret=config.polymarket_api_secret,
        _base_url=config.polymarket_base_url
    )
    await polymarket_client.initialize()

    # Initialize bot manager
    logger.info("Initializing bot manager")
    bot_manager = BotManager(
        _polymarket_client=polymarket_client,
        _db_manager=db_manager
    )

    # Make instances available to routes
    app.state.db_manager = db_manager
    app.state.polymarket_client = polymarket_client
    app.state.bot_manager = bot_manager

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Cleanup bot manager
    if bot_manager is not None:
        await bot_manager.cleanup()

    # Close Polymarket client
    if polymarket_client is not None:
        await polymarket_client.close()

    # Close database
    if db_manager is not None:
        await db_manager.close()

    logger.info("Application shutdown complete")


# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="BotForm2",
    description="Multi-bot copy trading platform for Polymarket",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware for development
if config.is_development == True:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Security headers middleware
@app.middleware("http")
async def add_security_headers(_request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(_request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Authentication middleware
@app.middleware("http")
async def auth_middleware(_request: Request, call_next):
    """Require authentication for protected routes."""
    # Public routes that don't require authentication
    public_routes = [
        "/health",
        "/api/auth/login",
        "/api/auth/session",
        "/login",
        "/static",
        "/bg.mp4"
    ]

    # Check if route is public
    is_public = False
    i = 0
    for route in public_routes:
        if _request.url.path.startswith(route) == True:
            is_public = True
            break
        i = i + 1

    if is_public == False:
        # Require authentication
        session_token = _request.cookies.get('session_token')
        username = auth_manager.validate_session(session_token)

        if username is None:
            # Redirect to login for HTML pages
            if _request.url.path.startswith('/api') == True:
                raise HTTPException(status_code=401, detail="Not authenticated")
            else:
                return RedirectResponse(url="/login", status_code=303)

    return await call_next(_request)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")


# Video background route
@app.get("/bg.mp4")
async def get_background_video():
    """Serve background video."""
    video_path = os.path.join(os.getcwd(), "bg.mp4")
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4")
    else:
        logger.error("Background video not found at: {}".format(video_path))
        raise HTTPException(status_code=404, detail="Video not found")

# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page."""
    return templates.TemplateResponse("login.html", {"request": request})


# Homepage route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Serve homepage."""
    session_token = request.cookies.get('session_token')
    user_info = auth_manager.get_user_info(session_token)
    username = user_info.get('username') if user_info is not None else None
    role = user_info.get('role', 'guest') if user_info is not None else 'guest'
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": username,
        "role": role,
        "is_admin": True if role == 'admin' else False
    })


# Bot detail page route
@app.get("/bot/{bot_id}", response_class=HTMLResponse)
async def bot_detail_page(request: Request, bot_id: str):
    """Serve bot detail page."""
    session_token = request.cookies.get('session_token')
    user_info = auth_manager.get_user_info(session_token)
    username = user_info.get('username') if user_info is not None else None
    role = user_info.get('role', 'guest') if user_info is not None else 'guest'
    return templates.TemplateResponse("bot_detail.html", {
        "request": request,
        "bot_id": bot_id,
        "username": username,
        "role": role,
        "is_admin": True if role == 'admin' else False
    })


# Settings page route (admin only)
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Serve admin settings page."""
    session_token = request.cookies.get('session_token')
    user_info = auth_manager.get_user_info(session_token)

    if user_info is None:
        return RedirectResponse(url="/login", status_code=303)

    role = user_info.get('role', 'guest')

    # Only admins can access settings
    if role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    username = user_info.get('username')
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "username": username,
        "role": role,
        "is_admin": True
    })


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": config.env
    }


# Include API routes (after page routes to avoid conflicts)
app.include_router(auth_routes.router)
app.include_router(routes.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        reload=config.is_development
    )

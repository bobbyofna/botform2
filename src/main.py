"""
FastAPI application entry point for BotForm2.

Main web server and API implementation.
"""

import logging
import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import config
from .database.manager import DatabaseManager
from .api.polymarket import PolymarketClient
from .bots.bot_manager import BotManager
from .utils.vpn_check import VPNChecker
from .api import routes

# Fix Windows asyncio event loop for psycopg
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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


# Create FastAPI app
app = FastAPI(
    title="BotForm2",
    description="Multi-bot copy trading platform for Polymarket",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for development
if config.is_development == True:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(routes.router)


# Homepage route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Serve homepage."""
    return templates.TemplateResponse("index.html", {"request": request})


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": config.env
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        reload=config.is_development
    )

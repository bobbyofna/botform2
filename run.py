"""
Server startup script for BotForm2.

Runs the FastAPI application using uvicorn.
"""

import uvicorn
from src.config import config

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        reload=config.is_development,
        log_config=None
    )

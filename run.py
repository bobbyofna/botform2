"""
Server startup script for BotForm2.

Configures Windows event loop properly for psycopg.
"""

import asyncio
import sys

# Fix Windows event loop for psycopg before importing anything else
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable reload to avoid event loop issues
        log_level="info"
    )

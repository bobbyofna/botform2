# Server Management Commands

## Important: Use Makefile Commands Only

**ALL server operations MUST use the following Makefile commands:**

- `sudo make start` - Start the server
- `sudo make stop` - Stop the server
- `sudo make reload` - Restart the server

## Do NOT Use

- Direct Python/uvicorn commands
- Batch files (start.bat, stop.bat, restart.bat, etc.)
- Manual process management commands
- Any other server control methods

## Why

The Makefile provides a standardized interface for server management that:
- Ensures consistent behavior across the project
- Handles process management correctly
- Provides a single source of truth for server operations
- Works reliably on the Windows development environment

## Additional Commands

Run `sudo make help` to see all available Makefile commands.

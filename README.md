# BotForm2 - Polymarket Copy Trading Platform

A multi-bot copy trading platform for Polymarket with web-based management interface.

## Features

- **Copy Trading Bots**: Automatically copy trades from successful Polymarket traders
- **Paper & Production Modes**: Test strategies safely before going live
- **Web Interface**: Manage all bots through an elegant web dashboard
- **Real-time Monitoring**: Track performance and adjust parameters on the fly
- **Risk Management**: Built-in stop-loss and daily loss limits

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 12 or higher
- VPN (optional, can be disabled in settings)

## Installation

### 1. Clone and Setup Virtual Environment

```bash
cd c:\Users\Bobby\Documents\_BOTS\botform2
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

Dependencies are already installed in your venv. If you need to reinstall:

```bash
pip install -r requirements.txt
```

### 3. Configure PostgreSQL Database

**Option A: Install PostgreSQL Locally**

1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Create database:

```sql
CREATE DATABASE botform2;
CREATE USER botuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE botform2 TO botuser;
```

**Option B: Use Docker (Recommended for Development)**

```bash
docker run --name botform2-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=botform2 \
  -p 5432:5432 \
  -d postgres:15
```

### 4. Configure Environment Variables

Copy the example environment file and edit it:

```bash
copy .env.example .env
```

Edit `.env` and update:

```env
DATABASE_URL=postgresql://botuser:your_password@localhost:5432/botform2
POLYMARKET_API_KEY=your_api_key
POLYMARKET_API_SECRET=your_api_secret
REQUIRE_VPN=false  # Set to true if you want VPN enforcement
```

## Running the Application

### Start the Server

```bash
# Make sure you're in the project directory and venv is activated
cd c:\Users\Bobby\Documents\_BOTS\botform2
venv\Scripts\activate
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Or use the shorthand:

```bash
python -m src.main
```

### Access the Web Interface

Open your browser and navigate to:

```
http://127.0.0.1:8000
```

## Usage

### Creating a Bot

1. Click "+ New Bot" on the dashboard
2. Enter a name for your bot
3. Paste the Polymarket user URL you want to copy (e.g., `https://polymarket.com/user/0x1234...`)
4. Click "Create"

### Starting a Bot

- **Paper Mode**: Test without real money
- **Production Mode**: Execute real trades (requires API credentials)

### Monitoring

- View all bots on the dashboard
- Check individual bot performance
- View trade history
- Adjust parameters in real-time

## API Documentation

### Endpoints

#### Get All Bots
```
GET /api/bots
Query params: status (optional), sort_by (optional)
```

#### Create Bot
```
POST /api/bots
Body: {
  "name": "MyBot",
  "bot_type": "copy",
  "target_user_url": "https://polymarket.com/user/0x...",
  "max_trade_value": 500.0,
  "min_trade_value": 50.0,
  "copy_ratio": 0.5
}
```

#### Start Bot
```
POST /api/bots/{bot_id}/start
Body: {"mode": "paper" | "production"}
```

#### Stop Bot
```
POST /api/bots/{bot_id}/stop
```

#### Get Bot Trades
```
GET /api/bots/{bot_id}/trades?limit=50&offset=0
```

## Architecture

### Directory Structure

```
botform2/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database/            # Database layer
│   │   ├── manager.py       # Database operations
│   │   └── schema.sql       # Database schema
│   ├── api/
│   │   ├── polymarket.py    # Polymarket API client
│   │   └── routes.py        # FastAPI routes
│   ├── bots/
│   │   ├── base_bot.py      # Base bot class
│   │   ├── copy_bot.py      # Copy trading bot
│   │   └── bot_manager.py   # Bot lifecycle management
│   ├── models/              # Data models
│   └── utils/               # Utilities (VPN check, ID generation)
├── templates/               # HTML templates
├── static/                  # Static assets (JS, CSS)
└── requirements.txt         # Python dependencies
```

### Technology Stack

- **Backend**: FastAPI + Python asyncio
- **Database**: PostgreSQL with psycopg3
- **Frontend**: Vanilla JavaScript + Tailwind CSS + Chart.js
- **API Client**: httpx (async)

## Development

### Coding Style

This project follows the bobbyofna coding style:

- Underscore-prefixed constructor parameters (`_id`, `_name`)
- Explicit boolean comparisons (`== True`, `== False`)
- Property-heavy design with `@property` decorators
- String formatting with `.format()`, no f-strings
- Manual iteration with index tracking (`i = i + 1`)

### Adding New Bot Types

1. Create new bot class inheriting from `BaseBot`
2. Implement `_run_loop()` and `execute_trade()` methods
3. Register in `BotManager.create_bot()`

## Troubleshooting

### Database Connection Failed

**Error**: `Could not connect to database`

**Solution**:
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Ensure database exists: `psql -U postgres -c "CREATE DATABASE botform2;"`

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### VPN Check Failing

**Error**: `VPN validation failed`

**Solution**:
- Set `REQUIRE_VPN=false` in `.env` for development
- Or configure allowed VPN IPs in `ALLOWED_VPN_IPS`

## Security Notes

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use VPN** when running in production mode
3. **API Keys**: Keep Polymarket API keys secure
4. **Database**: Use strong passwords for production

## Testing

### Manual Testing

```bash
# Test API directly
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/bots

# Create a test bot
curl -X POST http://127.0.0.1:8000/api/bots \
  -H "Content-Type: application/json" \
  -d '{"name":"TestBot","bot_type":"copy","target_user_url":"https://polymarket.com/user/0xtest"}'
```

## Future Enhancements

- [ ] More bot types (arbitrage, momentum)
- [ ] Backtesting with historical data
- [ ] Email/SMS notifications
- [ ] Advanced analytics dashboard
- [ ] Mobile app
- [ ] Multi-exchange support

## License

Private project - All rights reserved

## Support

For issues or questions, check:
- Database connection
- Environment variables
- Log files (console output)

---

**Note**: This is a trading bot platform. Only use with money you can afford to lose. No guarantees of profit. Always test in paper mode first.

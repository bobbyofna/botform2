# BotForm2 Project Specification

## Project Overview
BotForm2 is a multi-bot copy trading platform for Polymarket that provides both API and web-based interfaces for managing cryptocurrency prediction market trading bots. The system enables users to create, configure, and monitor multiple copy-trading bots that mimic successful Polymarket traders, with support for both paper testing and production modes.

## Core Philosophy
- **Simplicity First**: Streamlined codebase focused on core functionality
- **Web-First Interface**: Primary interaction through elegant, graphical web UI
- **Live Management**: No code restarts required for bot management
- **Asynchronous Architecture**: Low-latency bot operations using asyncio
- **Database-Driven**: PostgreSQL for all persistent data and state management

## Technology Stack

### Backend
- **Language**: Python
- **Web Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg
- **Async Runtime**: asyncio
- **API Client**: httpx (async HTTP client for Polymarket API)
- **Environment**: python-dotenv for configuration

### Frontend
- **Framework**: Modern vanilla JavaScript with Fetch API
- **Styling**: Tailwind CSS (via CDN)
- **Charts**: Chart.js for performance graphs
- **UI Components**: Custom components with responsive design

### Security & Infrastructure
- **VPN Check**: Mandatory VPN validation on startup
- **API Rate Limiting**: Respect Polymarket API limits
- **Environment Variables**: Secure credential management

## System Architecture

### Directory Structure
```
botform2/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── database/
│   │   ├── __init__.py
│   │   ├── manager.py          # Database connection and operations manager
│   │   └── schema.sql          # Database schema definition
│   ├── api/
│   │   ├── __init__.py
│   │   ├── polymarket.py       # Polymarket API client wrapper
│   │   └── routes.py           # FastAPI route definitions
│   ├── bots/
│   │   ├── __init__.py
│   │   ├── base_bot.py         # Base bot class (abstract)
│   │   ├── copy_bot.py         # Copy trading bot implementation
│   │   └── bot_manager.py      # Bot lifecycle and thread management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── bot.py              # Bot data models
│   │   ├── trade.py            # Trade data models
│   │   └── performance.py      # Performance metrics models
│   └── utils/
│       ├── __init__.py
│       ├── vpn_check.py        # VPN validation utilities
│       └── id_generator.py     # Unique ID generation
├── static/
│   ├── css/
│   │   └── styles.css          # Custom CSS (minimal, Tailwind-first)
│   ├── js/
│   │   ├── main.js             # Homepage functionality
│   │   ├── bot_detail.js       # Individual bot page functionality
│   │   ├── bot_create.js       # Bot creation page functionality
│   │   └── charts.js           # Chart.js configuration and utilities
│   └── index.html              # Main page template
├── templates/
│   ├── index.html              # Homepage
│   ├── bot_detail.html         # Individual bot page
│   └── bot_create.html         # Bot creation page
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies
└── README.md                   # Setup and usage instructions
```

## Database Schema

### Tables

#### `bots`
```sql
CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    bot_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'inactive', 'paper', 'production'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Copy bot specific fields
    target_user_url TEXT,
    target_user_address VARCHAR(255),
    
    -- Parameters
    max_trade_value DECIMAL(10, 2),
    min_trade_value DECIMAL(10, 2),
    copy_ratio DECIMAL(5, 4),
    stop_loss_percentage DECIMAL(5, 2),
    max_daily_loss DECIMAL(10, 2),
    
    -- Notes
    notes TEXT,
    
    -- Performance tracking
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_profit DECIMAL(10, 2) DEFAULT 0.00,
    total_loss DECIMAL(10, 2) DEFAULT 0.00
);
```

#### `trades`
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    bot_id VARCHAR(50) REFERENCES bots(bot_id) ON DELETE CASCADE,
    
    -- Trade details
    is_paper_trade BOOLEAN NOT NULL,
    market_id VARCHAR(255),
    outcome VARCHAR(50),
    amount DECIMAL(10, 2),
    price DECIMAL(10, 6),
    
    -- Timestamps
    opened_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    
    -- Results
    profit_loss DECIMAL(10, 2),
    status VARCHAR(50) NOT NULL,  -- 'open', 'closed', 'cancelled'
    
    -- Copy trading link
    source_trade_id VARCHAR(255),  -- ID of the trade being copied
    target_trade_id VARCHAR(255)   -- ID of the original trader's trade
);
```

#### `performance_snapshots`
```sql
CREATE TABLE performance_snapshots (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(50) REFERENCES bots(bot_id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    total_profit DECIMAL(10, 2),
    total_trades INTEGER,
    win_rate DECIMAL(5, 2),
    
    -- For aggregated snapshots
    snapshot_type VARCHAR(50)  -- 'hourly', 'daily', 'weekly'
);
```

## Core Classes

### 1. BaseBot (Abstract Base Class)
**File**: `src/bots/base_bot.py`

**Purpose**: Foundation for all bot types with common functionality

**Key Properties**:
- `_id`: Unique bot identifier (7-digit random integer)
- `_type`: Bot type identifier (1 = CopyBot)
- `name`: Human-readable bot name
- `status`: Current bot status ('inactive', 'paper', 'production')
- `parameters`: Dictionary of bot-specific parameters
- `is_paper_mode`: Boolean indicating paper trading mode

**Key Methods**:
- `start()`: Initialize and start bot operations
- `stop()`: Gracefully stop bot operations
- `update_parameters()`: Update bot configuration
- `log_trade()`: Record trade to database
- `get_performance()`: Retrieve performance metrics

**Async Operations**:
- All bot operations run in asyncio event loop
- Each bot maintains its own async task

### 2. CopyBot (Inherits BaseBot)
**File**: `src/bots/copy_bot.py`

**Purpose**: Copy trades from specified Polymarket user

**Additional Properties**:
- `target_user_url`: URL of user to copy
- `target_user_address`: Extracted wallet address
- `copy_ratio`: Multiplier for trade amounts (e.g., 0.5 = 50% of original)
- `max_trade_value`: Maximum amount per trade
- `min_trade_value`: Minimum amount per trade
- `stop_loss_percentage`: Auto-exit threshold
- `max_daily_loss`: Daily loss limit
- `active_trades`: Dictionary mapping source trades to our trades

**Key Methods**:
- `extract_user_address()`: Parse wallet address from URL
- `poll_user_activity()`: Async loop to monitor target user
- `execute_copy_trade()`: Mirror a detected trade
- `close_position()`: Exit position when source closes
- `check_stop_loss()`: Monitor and enforce stop losses

**Polling Strategy**:
- Check for new trades every 5 seconds during active market hours
- Use Polymarket API endpoint: `/users/{address}/activity`
- Implement exponential backoff on rate limit errors
- Track last seen trade timestamp to avoid duplicates

### 3. DatabaseManager
**File**: `src/database/manager.py`

**Purpose**: Centralized database operations with connection pooling

**Key Properties**:
- `pool`: asyncpg connection pool
- `_instance`: Singleton instance

**Key Methods**:
- `initialize()`: Create connection pool and tables
- `execute()`: Execute write operations
- `fetch()`: Fetch single row
- `fetch_all()`: Fetch multiple rows
- `create_bot()`: Insert new bot record
- `update_bot()`: Update bot configuration
- `get_bot()`: Retrieve bot by ID
- `get_all_bots()`: Retrieve all bots with filters
- `record_trade()`: Insert trade record
- `get_bot_trades()`: Retrieve trades for specific bot
- `update_performance()`: Update bot performance metrics

### 4. PolymarketClient
**File**: `src/api/polymarket.py`

**Purpose**: Async HTTP client for Polymarket API interactions

**Key Properties**:
- `base_url`: Polymarket API base URL
- `client`: httpx AsyncClient instance
- `rate_limit_delay`: Minimum delay between requests

**Key Methods**:
- `get_user_activity()`: Fetch recent trades for a user
- `get_market_info()`: Retrieve market details
- `place_order()`: Execute a trade (production mode)
- `cancel_order()`: Cancel pending order
- `get_positions()`: Retrieve active positions
- `handle_rate_limit()`: Manage API rate limiting

**Rate Limiting**:
- Polymarket allows ~10 requests per second per IP
- Implement 200ms minimum delay between requests
- Use exponential backoff: 1s, 2s, 4s, 8s on 429 errors
- Track request timestamps globally across all bots

### 5. BotManager
**File**: `src/bots/bot_manager.py`

**Purpose**: Manage bot lifecycle and threading

**Key Properties**:
- `active_bots`: Dictionary of running bot instances
- `bot_tasks`: Dictionary of asyncio tasks

**Key Methods**:
- `create_bot()`: Instantiate new bot from parameters
- `start_bot()`: Launch bot in separate async task
- `stop_bot()`: Gracefully terminate bot
- `restart_bot()`: Stop and restart with new parameters
- `get_bot_status()`: Retrieve bot runtime status
- `cleanup()`: Shutdown all bots on application exit

## Web Interface Specifications

### Homepage (`/`)

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│  BotForm2 Dashboard                     [+ New Bot] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Paper Trading Performance (All Bots)                │
│  ┌────────────────────────────────────────────────┐ │
│  │                                                 │ │
│  │         [Chart.js Line Graph]                  │ │
│  │                                                 │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Production Performance (All Bots)                   │
│  ┌────────────────────────────────────────────────┐ │
│  │                                                 │ │
│  │         [Chart.js Line Graph]                  │ │
│  │                                                 │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Performance Metrics                                 │
│  ┌───────────┬───────────┬───────────┬───────────┐ │
│  │Total P/L  │Win Rate   │Total Bots │Active Bots│ │
│  │ +$1,234   │   67.5%   │     12    │     8     │ │
│  └───────────┴───────────┴───────────┴───────────┘ │
│                                                      │
│  Bot List                 [Filter: All ▼] [Sort ▼] │
│  ┌────────────────────────────────────────────────┐ │
│  │ 🟢 BitcoinCopy1    Paper    +$234.50    →     │ │
│  │ 🟢 BitcoinCopy2    Prod     +$567.89    →     │ │
│  │ 🔴 TestBot1        Inactive  $0.00      →     │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Features**:
- Real-time graph updates (fetch every 30 seconds)
- Filter dropdown: All / Inactive / Paper / Production
- Sort dropdown: Name / Profit (High-Low) / Profit (Low-High) / Created Date
- Click bot row to navigate to detail page
- Responsive grid layout

### Bot Detail Page (`/bot/{bot_id}`)

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│  ← Back to Dashboard          BitcoinCopy1          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Performance Graph        [MAX ▼] [1Y] [3M] [1M]...│
│  ┌────────────────────────────────────────────────┐ │
│  │                                                 │ │
│  │         [Chart.js Line Graph]                  │ │
│  │                                                 │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Status: 🟢 Running (Paper Mode)                    │
│  Total P/L: +$234.50 | Win Rate: 71.4%             │
│                                                      │
│  ┌────────┬─────────────┬──────────────┬──────────┐ │
│  │ [Stop] │[Start Paper]│[Start Prod]  │ [Edit]   │ │
│  └────────┴─────────────┴──────────────┴──────────┘ │
│                                                      │
│  Bot Parameters                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Max Trade Value ($) [?]  [   500.00   ]       │ │
│  │ Min Trade Value ($) [?]  [    50.00   ]       │ │
│  │ Copy Ratio [?]           [    0.50    ]       │ │
│  │ Stop Loss (%) [?]        [    10.00   ]       │ │
│  │ Max Daily Loss ($) [?]   [  1000.00   ]       │ │
│  │                                                 │ │
│  │ Target User: polymarket.com/user/0x1234...     │ │
│  │                                                 │ │
│  │                        [Save Changes]          │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Notes                                               │
│  ┌────────────────────────────────────────────────┐ │
│  │ This bot copies Bitcoin 15min bets from        │ │
│  │ top trader. Started 2024-01-15.                │ │
│  │ (Auto-saves as you type...)                    │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Parameter Tooltips** (appears on hover over `[?]`):
- **Max Trade Value**: Maximum dollar amount for any single trade
- **Min Trade Value**: Minimum dollar amount to execute a trade
- **Copy Ratio**: Multiplier for copied trade amounts (1.0 = exact copy, 0.5 = half)
- **Stop Loss**: Percentage loss threshold for automatic position exit
- **Max Daily Loss**: Maximum total loss allowed in a 24-hour period

**Features**:
- Auto-save notes with 2-second debounce
- Real-time parameter validation
- Disable editing when bot is running
- Confirm dialog before stopping production bots

### Bot Creation Page (`/create`)

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│  ← Back to Dashboard          Create New Bot        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Bot Configuration                                   │
│  ┌────────────────────────────────────────────────┐ │
│  │ Bot Name *                                      │ │
│  │ [                                    ]          │ │
│  │                                                 │ │
│  │ Bot Type *                                      │ │
│  │ [Copy Trading Bot ▼]  (only option for now)   │ │
│  │                                                 │ │
│  │ Target User URL *                               │ │
│  │ [https://polymarket.com/user/...]              │ │
│  │                                                 │ │
│  │ Max Trade Value ($) [?]                        │ │
│  │ [     500.00     ]                             │ │
│  │                                                 │ │
│  │ Min Trade Value ($) [?]                        │ │
│  │ [      50.00     ]                             │ │
│  │                                                 │ │
│  │ Copy Ratio [?]                                 │ │
│  │ [      0.50      ]                             │ │
│  │                                                 │ │
│  │ Stop Loss (%) [?]                              │ │
│  │ [      10.00     ]                             │ │
│  │                                                 │ │
│  │ Max Daily Loss ($) [?]                         │ │
│  │ [    1000.00     ]                             │ │
│  │                                                 │ │
│  │ ┌─────────────────────────────────────────────┐│ │
│  │ │[Save Inactive] [Start Paper] [Start Prod]  ││ │
│  │ └─────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Validation**:
- Required fields: Name, Type, Target User URL
- URL format validation for target user
- Numeric validation for all dollar/percentage fields
- Confirm dialog before starting in production mode

## API Endpoints

### Bot Management

**GET** `/api/bots`
- Query params: `status` (optional), `sort_by` (optional)
- Returns: Array of bot objects

**POST** `/api/bots`
- Body: Bot configuration object
- Returns: Created bot object with ID

**GET** `/api/bots/{bot_id}`
- Returns: Detailed bot object with performance data

**PUT** `/api/bots/{bot_id}`
- Body: Updated bot parameters
- Returns: Updated bot object

**DELETE** `/api/bots/{bot_id}`
- Returns: Success confirmation

**POST** `/api/bots/{bot_id}/start`
- Body: `{"mode": "paper" | "production"}`
- Returns: Bot status

**POST** `/api/bots/{bot_id}/stop`
- Returns: Bot status

### Performance Data

**GET** `/api/performance/aggregate`
- Query params: `mode` (paper/production), `period` (1d, 7d, 30d, all)
- Returns: Time-series performance data for charts

**GET** `/api/bots/{bot_id}/performance`
- Query params: `period` (24h, 1w, 1m, 3m, 1y, max)
- Returns: Bot-specific performance time-series

**GET** `/api/bots/{bot_id}/trades`
- Query params: `limit`, `offset`
- Returns: Paginated trade history

### Notes

**PUT** `/api/bots/{bot_id}/notes`
- Body: `{"notes": "text content"}`
- Returns: Success confirmation

## Security & Configuration

### Environment Variables (`.env`)
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/botform2

# Polymarket API
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_API_SECRET=your_api_secret_here

# Security
REQUIRE_VPN=true
ALLOWED_VPN_IPS=203.0.113.0/24,198.51.100.0/24

# Application
ENV=development  # development | production
LOG_LEVEL=INFO
```

### VPN Check Implementation
**File**: `src/utils/vpn_check.py`

**Requirements**:
1. Check public IP address on startup
2. Verify IP is within allowed VPN ranges
3. Block application startup if VPN not detected
4. Log VPN status and IP information

**Implementation**:
```python
def check_vpn_status():
    # Fetch public IP from ipify or similar service
    # Compare against ALLOWED_VPN_IPS from .env
    # Return True if match, False otherwise
    # If REQUIRE_VPN == True and check fails, exit(1)
```

## Copy Bot Trading Logic

### Monitoring Flow
1. Bot polls target user's activity endpoint every 5 seconds
2. Detect new trades by comparing timestamps
3. Extract trade details: market, outcome, amount, price
4. Validate against bot parameters (min/max amounts)
5. Execute copy trade via Polymarket API (or log if paper mode)
6. Store trade mapping in database (source_trade_id → our_trade_id)

### Position Management
1. Continuously monitor source user's open positions
2. Detect when source closes position
3. Look up our corresponding position via trade mapping
4. Close our position immediately
5. Record P/L and update performance metrics

### Risk Management
1. **Stop Loss**: Check each open position against stop_loss_percentage
   - Calculate current P/L percentage
   - Auto-close if loss exceeds threshold
   
2. **Daily Loss Limit**: Track total losses in rolling 24-hour window
   - Sum all losses from past 24 hours
   - Pause bot if max_daily_loss exceeded
   - Resume automatically when window expires

3. **Trade Size Limits**: 
   - Apply copy_ratio to source trade amount
   - Enforce min_trade_value (skip if below)
   - Cap at max_trade_value (reduce if above)

## Development Priorities

### Phase 1: Core Infrastructure (Week 1)
- [ ] Database schema and manager implementation
- [ ] FastAPI application skeleton
- [ ] Basic bot classes (BaseBot, CopyBot)
- [ ] Polymarket API client with rate limiting
- [ ] VPN validation on startup
- [ ] ID generation utilities

### Phase 2: Bot Functionality (Week 2)
- [ ] Copy bot polling mechanism
- [ ] Trade execution (paper mode)
- [ ] Position tracking and closing
- [ ] Risk management (stop loss, daily limits)
- [ ] Bot manager with asyncio task handling
- [ ] Performance metrics calculation

### Phase 3: Web Interface (Week 3)
- [ ] Homepage with charts and bot list
- [ ] Bot detail page with editing
- [ ] Bot creation page
- [ ] API endpoints for all features
- [ ] Real-time updates via polling
- [ ] Notes auto-save functionality

### Phase 4: Testing & Refinement (Week 4)
- [ ] End-to-end testing with paper mode
- [ ] Performance optimization
- [ ] Error handling and logging
- [ ] Documentation
- [ ] Production readiness checks

## Testing Strategy

### Paper Mode Testing
- Create copy bots pointing to active traders
- Monitor for 48 hours in paper mode
- Verify all trades are detected and "executed"
- Validate risk management triggers correctly
- Check P/L calculations match expected results

### Database Testing
- Verify all CRUD operations
- Test concurrent access from multiple bots
- Validate foreign key constraints
- Check performance with 1000+ trade records

### API Testing
- Test all endpoints with valid/invalid data
- Verify authentication (if implemented)
- Check error handling for malformed requests
- Load test with multiple concurrent bots

## Coding Standards (bobbyofna Style)

### Critical Style Requirements
1. **Underscore-prefixed parameters**: All constructor params use `_param` pattern
2. **Explicit boolean comparisons**: Always use `== True` or `== False`
3. **Property-heavy design**: Use `@property` for computed values, never cache
4. **Manual iteration**: Use indexed loops with `i = i + 1`, not `enumerate()`
5. **String formatting**: Use `.format()`, never f-strings
6. **List initialization**: `[] if _param is None else _param` pattern
7. **Ternary conditionals**: `return True if condition == True else False`
8. **Method chaining**: Return `self` for chainable methods

### Example Bot Class Structure
```python
class CopyBot:
    def __init__(self, _id, _name, _target_url, _parameters=None):
        self._id = _id
        self.name = _name
        self.target_url = _target_url
        self.parameters = {} if _parameters is None else _parameters
        self.active_trades = []
    
    @property
    def _type(self):
        return 1
    
    @property
    def is_running(self):
        return True if self.status == 'running' else False
    
    @property
    def total_profit(self):
        profit = 0
        i = 0
        for trade in self.active_trades:
            profit = profit + trade.profit_loss
            i = i + 1
        return profit
    
    def start(self):
        # Implementation
        return self
    
    def stop(self):
        # Implementation
        return self
```

## Success Metrics

### Functional Requirements
- ✓ Create/edit/delete bots via web interface without code restart
- ✓ Real-time monitoring of copy bot targets
- ✓ Accurate trade replication with configurable parameters
- ✓ Reliable stop-loss and risk management
- ✓ Clear performance visualization

### Performance Requirements
- Trade detection latency < 10 seconds
- Web UI updates < 2 seconds
- Database queries < 100ms for standard operations
- Support 10+ concurrent bots without degradation

### User Experience Requirements
- Intuitive web interface requiring no documentation
- Clear visual feedback for all actions
- Graceful error handling with helpful messages
- Mobile-responsive design

## Future Enhancements (Post-MVP)
- Additional bot types (momentum, arbitrage, etc.)
- Backtesting mode with historical data
- Advanced analytics and reporting
- Email/SMS notifications for key events
- Multi-exchange support
- Mobile app (React Native)
- Machine learning for trade optimization

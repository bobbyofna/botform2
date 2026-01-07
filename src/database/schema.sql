-- BotForm2 Database Schema

-- Bots table
CREATE TABLE IF NOT EXISTS bots (
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

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
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

-- Performance snapshots table
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(50) REFERENCES bots(bot_id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    total_profit DECIMAL(10, 2),
    total_trades INTEGER,
    win_rate DECIMAL(5, 2),

    -- For aggregated snapshots
    snapshot_type VARCHAR(50)  -- 'hourly', 'daily', 'weekly'
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bots_status ON bots(status);
CREATE INDEX IF NOT EXISTS idx_bots_bot_id ON bots(bot_id);
CREATE INDEX IF NOT EXISTS idx_trades_bot_id ON trades(bot_id);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at);
CREATE INDEX IF NOT EXISTS idx_performance_bot_id ON performance_snapshots(bot_id);
CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_snapshots(timestamp);

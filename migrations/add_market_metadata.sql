-- Migration: Add market metadata fields to trades table
-- Date: 2026-01-08
-- Description: Adds market_name and close_value fields to improve trade display

-- Add market_name column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'trades' AND column_name = 'market_name'
    ) THEN
        ALTER TABLE trades ADD COLUMN market_name TEXT;
    END IF;
END $$;

-- Expand outcome column to support longer names
DO $$
BEGIN
    ALTER TABLE trades ALTER COLUMN outcome TYPE VARCHAR(255);
END $$;

-- Add close_value column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'trades' AND column_name = 'close_value'
    ) THEN
        ALTER TABLE trades ADD COLUMN close_value DECIMAL(10, 2);
    END IF;
END $$;

-- Add comments for clarity
COMMENT ON COLUMN trades.market_name IS 'Descriptive name of what the bet was on';
COMMENT ON COLUMN trades.outcome IS 'Outcome name (YES/NO or player name, etc.)';
COMMENT ON COLUMN trades.amount IS 'Initial bet amount';
COMMENT ON COLUMN trades.price IS 'Entry price';
COMMENT ON COLUMN trades.exit_price IS 'Exit price when closed';
COMMENT ON COLUMN trades.close_value IS 'Total value when position was closed';

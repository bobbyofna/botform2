-- Migration to add wallet balance columns to bots table
-- Run this if your database already exists

-- Add paper trading wallet columns to bots table
ALTER TABLE bots
ADD COLUMN IF NOT EXISTS paper_wallet_balance DECIMAL(10, 2) DEFAULT 1000.00,
ADD COLUMN IF NOT EXISTS paper_wallet_initial DECIMAL(10, 2) DEFAULT 1000.00;

-- Add exit_price column to trades table
ALTER TABLE trades
ADD COLUMN IF NOT EXISTS exit_price DECIMAL(10, 6);

-- Update existing bots to have default wallet balance
UPDATE bots
SET paper_wallet_balance = 1000.00,
    paper_wallet_initial = 1000.00
WHERE paper_wallet_balance IS NULL;

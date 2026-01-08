# Database Setup Guide for Ubuntu

This guide explains how to complete the database setup for BotForm2 on your Ubuntu EC2 instance.

## Current Status

You've already completed:
- ✓ PostgreSQL installed
- ✓ User `botform` created
- ✓ Database `botform2` created

## What You Need to Do

### 1. Update the .env file with your database password

Edit `.env` and replace `YOUR_PASSWORD_HERE` with the actual password for the `botform` database user:

```bash
DATABASE_URL=postgresql://botform:YOUR_ACTUAL_PASSWORD@localhost:5432/botform2
```

### 2. Set up .pgpass for seamless psql access

This allows me (Claude) to run PostgreSQL commands without being prompted for passwords.

Create or append to `~/.pgpass`:

```bash
echo "localhost:5432:botform2:botform:YOUR_ACTUAL_PASSWORD" >> ~/.pgpass
chmod 600 ~/.pgpass
```

Replace `YOUR_ACTUAL_PASSWORD` with the actual password.

### 3. Run the database setup script

The updated `setup_database.py` script will:
- Verify the user and database exist (won't recreate them)
- Create all required tables with the current schema
- Set up indexes for performance

Run it with:

```bash
python3 setup_database.py
```

Or if you have permission issues:

```bash
sudo -u postgres python3 setup_database.py
```

## What Changed in setup_database.py

The script has been updated for Ubuntu:
- ✓ Reads credentials from `.env` file automatically
- ✓ Handles existing users/databases gracefully (no errors if they already exist)
- ✓ Uses peer authentication for local PostgreSQL connections
- ✓ Updated table schema matches current codebase:
  - `bots` table with all fields from Bot model
  - `trades` table with all fields from Trade model
  - `performance_snapshots` table for performance tracking
  - Proper indexes for query performance
- ✓ Provides Ubuntu-specific troubleshooting tips
- ✓ Shows how to set up `.pgpass` for seamless CLI access

## Alternative: Manual Table Creation

If you prefer to create tables manually using psql:

```bash
# Connect to your database
psql -U botform -d botform2

# Then run the schema file
\i src/database/schema.sql

# Verify tables were created
\dt

# Exit
\q
```

## Giving Claude Access to Run psql Commands

The best way to give me access to run PostgreSQL commands is through the `.pgpass` file (Step 2 above). This file:
- Is stored in your home directory (`~/.pgpass`)
- Contains database credentials in format: `host:port:database:username:password`
- Must have restricted permissions (600) for security
- Allows psql to authenticate without password prompts

Once set up, I can run commands like:
```bash
psql -U botform -d botform2 -c "SELECT * FROM bots;"
```

## Verification

After setup, verify everything works:

```bash
# Check if tables exist
psql -U botform -d botform2 -c "\dt"

# Check the schema
psql -U botform -d botform2 -c "\d bots"
```

## Current Schema

The database includes these tables:
- **bots** - Bot configurations and performance metrics
- **trades** - Individual trade records (both paper and production)
- **performance_snapshots** - Time-series performance data for charting

## Security Note

Your `.env` file contains sensitive credentials. Make sure:
- It's in `.gitignore` (already done)
- File permissions are restrictive: `chmod 600 .env`
- Never commit it to version control

# Database Setup Guide

## Quick Start

Run the setup script to automatically create your database:

```bash
cd c:\Users\Bobby\Documents\_BOTS\botform2
.\venv\Scripts\activate
python setup_database.py
```

## What the Script Does

The `setup_database.py` script will:

1. **Connect to PostgreSQL** - Asks for your postgres superuser password
2. **Create a new user** - Default: `botuser` (you can customize)
3. **Create the database** - Default: `botform2` (you can customize)
4. **Create all tables** - Runs the SQL schema automatically
5. **Show connection string** - Displays what to put in your `.env` file

## Interactive Prompts

The script will ask you:

1. **Postgres superuser password** - The password for the `postgres` user
   - If you don't know it, try pressing Enter (trust authentication)
   - Check your PostgreSQL installation notes

2. **New username** - Default: `botuser`
   - Press Enter to use default
   - Or type your preferred username

3. **New password** - Default: `botpass123`
   - Press Enter to use default
   - Or type a secure password

4. **Database name** - Default: `botform2`
   - Press Enter to use default
   - Or type your preferred database name

## After Running the Script

1. The script will display a `DATABASE_URL` connection string
2. Copy this connection string
3. Update your `.env` file:

```env
DATABASE_URL=postgresql://botuser:botpass123@localhost:5432/botform2
```

4. Restart your server:

```bash
python run.py
```

## Troubleshooting

### "Could not connect to PostgreSQL"

**Check if PostgreSQL is running:**
```bash
sc query postgresql-x64-18
```

If it's not running, start it:
```bash
sc start postgresql-x64-18
```

### "Password authentication failed"

Try these options:

1. **Find your postgres password:**
   - Check the installation notes from when you installed PostgreSQL
   - Look in `C:\Program Files\PostgreSQL\18\data\pg_hba.conf`

2. **Reset the postgres password:**
   - Open pgAdmin
   - Right-click on the postgres user
   - Select "Properties" > "Definition"
   - Set a new password

3. **Use trust authentication temporarily:**
   - Edit `pg_hba.conf`
   - Change `md5` to `trust` for localhost connections
   - Restart PostgreSQL service
   - Run the setup script
   - Change back to `md5` after setup

### "User already exists"

This is fine! The script will skip user creation and just use the existing user.

### "Database already exists"

This is fine! The script will skip database creation and just create the tables.

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Connect to PostgreSQL

Using pgAdmin or psql:

```sql
-- Connect to postgres database
psql -U postgres
```

### 2. Create User and Database

```sql
-- Create user
CREATE USER botuser WITH PASSWORD 'botpass123';

-- Create database
CREATE DATABASE botform2 OWNER botuser;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE botform2 TO botuser;
```

### 3. Create Tables

```sql
-- Connect to botform2 database
\c botform2

-- Run the schema file
\i src/database/schema.sql
```

### 4. Update .env

```env
DATABASE_URL=postgresql://botuser:botpass123@localhost:5432/botform2
```

## Verifying Setup

After setup, you can verify the database is ready:

1. **Check tables were created:**

```bash
python
>>> import psycopg
>>> conn = psycopg.connect("postgresql://botuser:botpass123@localhost:5432/botform2")
>>> cur = conn.cursor()
>>> cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
>>> print(cur.fetchall())
[('bots',), ('trades',), ('performance_snapshots',)]
```

2. **Start the server and check logs:**

```bash
python run.py
```

Look for:
```
INFO - Database connection pool initialized
INFO - Database tables created successfully
```

## Security Notes

- Change the default password `botpass123` to something secure
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`

## Need Help?

If you encounter issues:

1. Check that PostgreSQL 18 is running
2. Verify the port is 5432 (default)
3. Check Windows Firewall isn't blocking localhost connections
4. Review the PostgreSQL logs in `C:\Program Files\PostgreSQL\18\data\log`

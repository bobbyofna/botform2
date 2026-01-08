# BotForm2 Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
make install
```

Or manually:
```bash
venv/bin/pip3 install -r requirements.txt
```

### 2. Setup Initial Users

After the database is initialized, run:

```bash
make setup-users
```

Or manually:
```bash
venv/bin/python3 setup_initial_users.py
```

This creates two default users:
- **Admin**: username `admin`, password `admin123`
- **Guest**: username `guest`, password `guest123`

### 3. Start the Server

```bash
make start
```

### 4. Login and Change Passwords

1. Open your browser and navigate to your server (e.g., `http://your-server/login`)
2. Log in with admin credentials: `admin` / `admin123`
3. Click the hamburger menu (☰) in the top right
4. Select "Settings"
5. Change passwords for both admin and guest users

## Common Commands

```bash
# Install dependencies
make install

# Setup initial users
make setup-users

# Start the server
make start

# Stop the server
make stop

# Restart the server
make restart

# Check server status
make status

# View logs
make logs

# Reboot database and server
make reboot
```

## Troubleshooting

### Setup Script Errors

**Problem**: `ModuleNotFoundError: No module named 'psycopg_pool'`

**Solution**: Install dependencies first:
```bash
make install
```

**Problem**: `Error connecting to database`

**Solution**: Make sure PostgreSQL is running:
```bash
sudo systemctl start postgresql
```

### Can't Access Settings Page

**Problem**: "Admin access required" error

**Solution**: Make sure you're logged in as the admin user, not guest.

### Database Connection Issues

**Problem**: Can't connect to database

**Solution**:
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify database exists: `psql -U postgres -l | grep botform2`
3. Check connection string in `.env` file

## Features

### Admin Settings

Admins have access to a settings page where they can:
- View all users
- Add new users with admin or guest roles
- Change user passwords
- Delete users (except the main admin)

### User Roles

- **Admin**: Full access to all features
  - Create/manage bots
  - View all trades and performance
  - Access settings page
  - Manage user accounts

- **Guest**: Read-only access
  - View bots and performance
  - Cannot create/modify bots
  - Cannot access settings

## Security Notes

1. **Change default passwords immediately** after setup
2. **Use strong passwords** - consider using a password manager
3. **Limit admin accounts** - only give admin access to trusted users
4. **Backup your database** regularly
5. **Keep the system updated** - regularly update dependencies

## File Structure

```
botform2/
├── setup_initial_users.py  # User setup script
├── requirements.txt        # Python dependencies
├── Makefile               # Easy commands
├── venv/                  # Virtual environment
├── src/
│   ├── api/
│   │   ├── auth_routes.py # Authentication
│   │   └── routes.py      # User management API
│   ├── database/
│   │   ├── schema.sql     # Database schema (includes users table)
│   │   └── manager.py     # Database operations
│   └── utils/
│       └── auth.py        # Auth utilities
└── templates/
    └── settings.html      # Admin settings page
```

## Next Steps

1. Run the setup script: `make setup-users`
2. Start the server: `make start`
3. Login as admin and change passwords
4. Create your first bot!

For more detailed information, see [ADMIN_SETTINGS_GUIDE.md](ADMIN_SETTINGS_GUIDE.md).

# Admin Settings & User Management Guide

## Overview

BotForm2 now includes a comprehensive admin settings page where administrators can manage user accounts, change passwords, and add new users to the system.

## Features

### Admin Settings Page

When logged in as an admin, you'll see a "Settings" option in the hamburger menu (top right). This takes you to the admin settings page where you can:

1. **View all users** - See a list of all user accounts with their roles and creation dates
2. **Add new users** - Create new admin or guest accounts
3. **Change passwords** - Update passwords for any user account
4. **Delete users** - Remove user accounts (except the main admin account)

### User Roles

- **Admin**: Full access to all features including:
  - Creating and managing bots
  - Viewing all trades and performance data
  - Accessing the settings page
  - Managing user accounts

- **Guest**: Read-only access:
  - View bots and performance data
  - Cannot create or modify bots
  - Cannot access settings

## Setup Instructions

### 1. Database Migration

The new user management system stores credentials in the database instead of hardcoded values. Run the database setup script:

```bash
# Make sure the database is running
make db-up

# Run the initial user setup script
python3 setup_initial_users.py
```

This will create two default users:
- **Admin**: username `admin`, password `admin123`
- **Guest**: username `guest`, password `guest123`

**IMPORTANT**: Change these default passwords immediately after first login!

### 2. First Login

1. Navigate to the login page
2. Log in with the admin credentials:
   - Username: `admin`
   - Password: `admin123`

### 3. Change Default Passwords

1. Click the hamburger menu (☰) in the top right
2. Select "Settings"
3. In the user management table, click "Change Password" for each user
4. Set secure passwords for both admin and guest accounts

## Using the Settings Page

### Adding a New User

1. Go to Settings → Click "Add User" button
2. Enter the username (must be unique)
3. Enter a password
4. Select role (Admin or Guest)
5. Click "Save"

### Changing a Password

1. Go to Settings → Find the user in the table
2. Click "Change Password" next to their name
3. Enter the new password
4. Click "Save"

### Deleting a User

1. Go to Settings → Find the user in the table
2. Click "Delete" next to their name (not available for the main admin account)
3. Confirm the deletion

**Note**: You cannot delete the main admin account to prevent lockout.

## API Endpoints

The following API endpoints are available for user management (admin only):

- `GET /api/users` - List all users
- `POST /api/users` - Create a new user
- `PUT /api/users/{user_id}` - Update user (change password or role)
- `DELETE /api/users/{user_id}` - Delete a user

All endpoints require admin authentication and return appropriate error codes for unauthorized access.

## Security Features

- Passwords are hashed using bcrypt before storage
- Session-based authentication with secure cookies
- Brute force protection with automatic lockout
- Rate limiting on all API endpoints
- The main admin account cannot be deleted
- Database-backed credential storage (no hardcoded passwords)

## Troubleshooting

### Can't Access Settings Page

- Make sure you're logged in as an admin user
- Guest users cannot access the settings page
- Check that your session hasn't expired (refresh and log in again)

### Error Creating Users

- Ensure usernames are unique (no duplicates)
- Check database connection is active
- Verify you have admin privileges

### Database Connection Issues

```bash
# Check if the database is running
make db-status

# Restart the database if needed
make db-restart
```

## Database Schema

The users table structure:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'admin' or 'guest'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Best Practices

1. **Change default passwords immediately** after setup
2. **Use strong passwords** for all accounts
3. **Limit admin access** - only give admin role to trusted users
4. **Regular audits** - periodically review user accounts and remove unused ones
5. **Backup credentials** - keep a secure record of admin passwords
6. **Monitor access** - check logs for unauthorized access attempts

## Migration from Hardcoded Credentials

If you're upgrading from a version with hardcoded credentials:

1. Run `python3 setup_initial_users.py` to create database users
2. The old hardcoded credentials in `auth_routes.py` have been removed
3. All authentication now goes through the database
4. Existing sessions will remain valid during the transition

## Future Enhancements

Potential future features:
- Password reset via email
- Two-factor authentication (2FA)
- User activity logs
- Password complexity requirements
- Session management (view/revoke active sessions)
- User groups and custom permissions

#!/usr/bin/env python3
"""
Setup initial users for BotForm2.

Creates default admin and guest users if they don't already exist.
This should be run after the database schema is created.

Usage:
    python3 setup_initial_users.py
    OR
    ./venv/bin/python3 setup_initial_users.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def setup_initial_users():
    """Create initial admin and guest users."""
    print("Setting up initial users...")
    print("Importing modules...")

    try:
        from src.database.manager import DatabaseManager
        from src.config import config
    except ModuleNotFoundError as e:
        print(f"\n✗ Error: Missing required module: {e}")
        print("\nPlease install requirements first:")
        print("  venv/bin/pip3 install -r requirements.txt")
        print("\nOr activate the virtual environment:")
        print("  source venv/bin/activate")
        print("  pip3 install -r requirements.txt")
        sys.exit(1)

    # Initialize database
    print("Connecting to database...")
    db_manager = DatabaseManager.get_instance(_connection_string=config.database_url)

    try:
        await db_manager.initialize()
    except Exception as e:
        print(f"\n✗ Error connecting to database: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  sudo systemctl start postgresql")
        print("\nAnd that the database exists:")
        print("  psql -U postgres -c 'CREATE DATABASE botform2;'")
        sys.exit(1)

    try:
        # Check if admin user exists
        admin_user = await db_manager.get_user_by_username('admin')
        if admin_user is None:
            print("Creating admin user...")
            # Default admin password: admin123
            await db_manager.create_user(
                _username='admin',
                _password='admin123',
                _role='admin'
            )
            print("✓ Admin user created (username: admin, password: admin123)")
        else:
            print("✓ Admin user already exists")

        # Check if guest user exists
        guest_user = await db_manager.get_user_by_username('guest')
        if guest_user is None:
            print("Creating guest user...")
            # Default guest password: guest123
            await db_manager.create_user(
                _username='guest',
                _password='guest123',
                _role='guest'
            )
            print("✓ Guest user created (username: guest, password: guest123)")
        else:
            print("✓ Guest user already exists")

        print("\n" + "="*50)
        print("Initial users setup complete!")
        print("="*50)
        print("\nIMPORTANT: Please change the default passwords after first login!")
        print("\nDefault Credentials:")
        print("  Admin: username='admin', password='admin123'")
        print("  Guest: username='guest', password='guest123'")
        print("\nTo change passwords:")
        print("  1. Log in as admin at http://your-server/login")
        print("  2. Click the hamburger menu (☰) → Settings")
        print("  3. Click 'Change Password' for each user")
        print()

    except Exception as e:
        print(f"\n✗ Error setting up users: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(setup_initial_users())

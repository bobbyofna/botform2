#!/usr/bin/env python3
"""
Setup initial users for BotForm2.

Creates default admin and guest users if they don't already exist.
This should be run after the database schema is created.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.manager import DatabaseManager
from src.config import config


async def setup_initial_users():
    """Create initial admin and guest users."""
    print("Setting up initial users...")

    # Initialize database
    db_manager = DatabaseManager.get_instance(_connection_string=config.database_url)
    await db_manager.initialize()

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

        print("\nInitial users setup complete!")
        print("\nIMPORTANT: Please change the default passwords after first login!")
        print("  Admin: username='admin', password='admin123'")
        print("  Guest: username='guest', password='guest123'")

    except Exception as e:
        print(f"Error setting up users: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(setup_initial_users())

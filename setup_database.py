"""
Database setup script for BotForm2.

Creates PostgreSQL user, database, and tables.
Run this script once to initialize your database.

Ubuntu/Linux environment version.
"""

import sys
import os
import getpass
import psycopg
from psycopg import sql


def print_step(_message):
    """Print step message with formatting."""
    print("\n" + "=" * 60)
    print(_message)
    print("=" * 60)


def get_admin_credentials():
    """Get the database admin credentials."""
    print("\nTo create tables, we need to connect to the PostgreSQL database.")
    print("\nOptions:")
    print("1. Use credentials from .env file")
    print("2. Connect as 'postgres' superuser")
    print("3. Enter custom credentials\n")

    choice = input("Choose option [1]: ").strip() or "1"

    if choice == "1":
        return None, None  # Will use .env credentials
    elif choice == "2":
        password = getpass.getpass("Enter postgres password (or press Enter for peer auth): ")
        return "postgres", password if password != '' else None
    else:
        username = input("Username: ").strip()
        password = getpass.getpass("Password (or press Enter for peer auth): ")
        return username, password if password != '' else None


def create_database_and_user(_admin_username, _admin_password):
    """
    Create new database user and database (or verify they exist).

    Args:
        _admin_username: PostgreSQL admin username (None to use .env)
        _admin_password: PostgreSQL admin password

    Returns:
        Tuple of (username, password, database_name) or None if failed
    """
    print_step("STEP 1: Verifying Database User and Database")

    # Get user details from .env file if it exists
    env_username = None
    env_password = None
    env_database = None

    if os.path.exists('.env'):
        print("\nReading credentials from .env file...")
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    # Parse postgresql://username:password@host:port/database
                    db_url = line.strip().split('=', 1)[1]
                    if '://' in db_url:
                        creds_part = db_url.split('://')[1]
                        if '@' in creds_part:
                            user_pass = creds_part.split('@')[0]
                            if ':' in user_pass:
                                env_username, env_password = user_pass.split(':', 1)
                            env_database = creds_part.split('/')[-1]

    # Determine which credentials to use
    if _admin_username is None:
        # Use .env credentials
        if env_username is None or env_password is None or env_database is None:
            print("\n✗ ERROR: .env file is missing or incomplete DATABASE_URL")
            print("Please update .env with: DATABASE_URL=postgresql://username:password@localhost:5432/database")
            return None

        new_username = env_username
        new_password = env_password
        database_name = env_database
        print("\n✓ Using credentials from .env file")
        print("  Username: {}".format(new_username))
        print("  Database: {}".format(database_name))
    else:
        # Use provided admin credentials to create new user/database
        print("\nEnter details for the database user:")
        default_username = env_username if env_username is not None else "botform"
        default_database = env_database if env_database is not None else "botform2"

        new_username = input("Username [{}]: ".format(default_username)).strip() or default_username
        new_password = getpass.getpass("Password for user {}: ".format(new_username)).strip()
        database_name = input("Database name [{}]: ".format(default_database)).strip() or default_database

    print("\nAttempting to connect to PostgreSQL...")

    # Connection strings to try
    connection_strings = []

    # If using .env credentials, connect to the target database directly
    if _admin_username is None:
        connection_strings.append("postgresql://{}:{}@localhost:5432/{}".format(new_username, new_password, database_name))
    else:
        # Connect as admin to postgres database
        if _admin_password is not None:
            connection_strings.append("postgresql://{}:{}@localhost:5432/postgres".format(_admin_username, _admin_password))
        # Try without password (peer/trust authentication)
        connection_strings.append("postgresql://{}@localhost:5432/postgres".format(_admin_username))

    conn = None
    i = 0
    for conn_string in connection_strings:
        try:
            print("Trying connection method {}...".format(i + 1))
            conn = psycopg.connect(conn_string)
            print("✓ Connected successfully!")
            break
        except Exception as e:
            print("✗ Connection failed: {}".format(str(e)))
            i = i + 1

    if conn is None:
        print("\n✗ ERROR: Could not connect to PostgreSQL.")
        print("\nTroubleshooting for Ubuntu:")
        print("1. Make sure PostgreSQL is running: sudo systemctl status postgresql")
        print("2. Check your password in .env file is correct")
        print("3. Try running with option 2 as postgres user: sudo -u postgres python3 setup_database.py")
        print("4. Check pg_hba.conf for authentication settings")
        return None

    try:
        # Set autocommit for CREATE DATABASE
        conn.autocommit = True
        cursor = conn.cursor()

        # If we're using .env credentials, we're already connected to the target database
        # Just verify and skip user/database creation
        if _admin_username is None:
            print("\n✓ Successfully connected to database '{}' as user '{}'".format(database_name, new_username))
            cursor.close()
            conn.close()
            return (new_username, new_password, database_name)

        # Otherwise, create user and database if needed
        # Check if user exists
        print("\nChecking if user '{}' exists...".format(new_username))
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (new_username,)
        )
        user_exists = cursor.fetchone() is not None

        if user_exists == True:
            print("✓ User '{}' already exists".format(new_username))
        else:
            # Create user
            print("Creating user '{}'...".format(new_username))
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                    sql.Identifier(new_username),
                    sql.Literal(new_password)
                )
            )
            print("✓ User '{}' created successfully".format(new_username))

        # Check if database exists
        print("\nChecking if database '{}' exists...".format(database_name))
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database_name,)
        )
        db_exists = cursor.fetchone() is not None

        if db_exists == True:
            print("✓ Database '{}' already exists".format(database_name))
        else:
            # Create database
            print("Creating database '{}'...".format(database_name))
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database_name),
                    sql.Identifier(new_username)
                )
            )
            print("✓ Database '{}' created successfully".format(database_name))

        # Grant privileges
        print("\nGranting privileges...")
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(database_name),
                sql.Identifier(new_username)
            )
        )
        print("✓ Privileges granted")

        cursor.close()
        conn.close()

        return (new_username, new_password, database_name)

    except Exception as e:
        print("\n✗ ERROR: {}".format(str(e)))
        if conn is not None:
            conn.close()
        return None


def create_tables(_username, _password, _database):
    """
    Create database tables from schema.sql.

    Args:
        _username: Database username
        _password: Database password
        _database: Database name

    Returns:
        True if successful, False otherwise
    """
    print_step("STEP 2: Creating Database Tables")

    conn_string = "postgresql://{}:{}@localhost:5432/{}".format(
        _username, _password, _database
    )

    try:
        print("\nConnecting to database '{}'...".format(_database))
        conn = psycopg.connect(conn_string)
        cursor = conn.cursor()

        # Read schema file
        schema_file = "src/database/schema.sql"
        print("Reading schema from {}...".format(schema_file))

        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Execute schema
        print("Creating tables...")
        cursor.execute(schema_sql)
        conn.commit()

        print("✓ Tables created successfully!")

        # List created tables
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        tables = cursor.fetchall()
        print("\nCreated tables:")
        i = 0
        for table in tables:
            print("  - {}".format(table[0]))
            i = i + 1

        cursor.close()
        conn.close()

        return True

    except FileNotFoundError:
        print("\n✗ ERROR: Could not find schema.sql file")
        print("Make sure you're running this script from the project root directory")
        return False
    except Exception as e:
        print("\n✗ ERROR: {}".format(str(e)))
        return False


def print_env_config(_username, _password, _database):
    """
    Print the .env configuration.

    Args:
        _username: Database username
        _password: Database password
        _database: Database name
    """
    print_step("STEP 3: Update Your .env File")

    connection_string = "postgresql://{}:{}@localhost:5432/{}".format(
        _username, _password, _database
    )

    print("\nAdd this line to your .env file:")
    print("\n" + "-" * 60)
    print("DATABASE_URL={}".format(connection_string))
    print("-" * 60)

    print("\nYour .env file should look like this:")
    print("""
# Database Configuration
DATABASE_URL={}

# Polymarket API Configuration
POLYMARKET_API_KEY=
POLYMARKET_API_SECRET=
POLYMARKET_BASE_URL=https://api.polymarket.com

# Security Configuration
REQUIRE_VPN=false
ALLOWED_VPN_IPS=

# Application Configuration
ENV=development
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000

# Bot Configuration
POLL_INTERVAL=5
RATE_LIMIT_DELAY=0.2
""".format(connection_string))


def main():
    """Main setup function."""
    print("\n" + "=" * 60)
    print("BotForm2 Database Setup Script")
    print("=" * 60)

    print("\nThis script will:")
    print("1. Create a new PostgreSQL user")
    print("2. Create the botform2 database")
    print("3. Create all required tables")
    print("4. Show you the connection string for your .env file")

    response = input("\nContinue? (y/n): ").strip().lower()
    if response != 'y':
        print("\nSetup cancelled.")
        return

    # Get admin credentials
    admin_username, admin_password = get_admin_credentials()

    # Create user and database (or verify they exist)
    result = create_database_and_user(admin_username, admin_password)

    if result is None:
        print("\n✗ Database setup failed!")
        print("\nTroubleshooting for Ubuntu:")
        print("1. Make sure PostgreSQL is running: sudo systemctl status postgresql")
        print("2. Try running as postgres user: sudo -u postgres python3 setup_database.py")
        print("3. Check authentication settings in /etc/postgresql/*/main/pg_hba.conf")
        return

    username, password, database = result

    # Create tables
    success = create_tables(username, password, database)

    if success == False:
        print("\n✗ Table creation failed!")
        return

    # Print configuration
    print_env_config(username, password, database)

    print("\n" + "=" * 60)
    print("✓ Database Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update your .env file with the DATABASE_URL above (if not already done)")
    print("2. Save the database password to .pgpass for seamless CLI access:")
    print("   Run this command (copy-paste the entire line):")
    print("   echo 'localhost:5432:{}:{}:{}' >> ~/.pgpass && chmod 600 ~/.pgpass".format(database, username, password))
    print("\n   Note: The single quotes prevent shell interpretation of special characters")
    print("3. Restart your BotForm2 server")
    print("4. The application will now connect to the database successfully")
    print("\nTo restart the server:")
    print("  python3 run.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print("\n✗ UNEXPECTED ERROR: {}".format(str(e)))
        sys.exit(1)

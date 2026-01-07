"""
Database setup script for BotForm2.

Creates PostgreSQL user, database, and tables.
Run this script once to initialize your database.
"""

import sys
import getpass
import psycopg
from psycopg import sql


def print_step(_message):
    """Print step message with formatting."""
    print("\n" + "=" * 60)
    print(_message)
    print("=" * 60)


def get_postgres_admin_password():
    """Get the PostgreSQL admin password from user."""
    print("\nTo create a new database user, we need to connect as the")
    print("PostgreSQL superuser (usually 'postgres').")
    print("\nIf you don't know the password, check your PostgreSQL")
    print("installation notes or try leaving it blank.\n")

    password = getpass.getpass("Enter postgres superuser password (or press Enter to skip): ")
    return password if password != '' else None


def create_database_and_user(_admin_password):
    """
    Create new database user and database.

    Args:
        _admin_password: PostgreSQL admin password

    Returns:
        Tuple of (username, password, database_name) or None if failed
    """
    print_step("STEP 1: Creating Database User and Database")

    # Get new user details
    print("\nEnter details for the new database user:")
    new_username = input("Username [botuser]: ").strip() or "botuser"
    new_password = getpass.getpass("Password for new user [botpass123]: ").strip() or "botpass123"
    database_name = input("Database name [botform2]: ").strip() or "botform2"

    print("\nAttempting to connect to PostgreSQL...")

    # Connection strings to try
    connection_strings = []

    if _admin_password is not None:
        connection_strings.append("postgresql://postgres:{}@localhost:5432/postgres".format(_admin_password))

    # Try without password (trust authentication)
    connection_strings.append("postgresql://postgres@localhost:5432/postgres")

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
        print("Please check your PostgreSQL installation and password.")
        return None

    try:
        # Set autocommit for CREATE DATABASE
        conn.autocommit = True
        cursor = conn.cursor()

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

    # Get admin password
    admin_password = get_postgres_admin_password()

    # Create user and database
    result = create_database_and_user(admin_password)

    if result is None:
        print("\n✗ Database setup failed!")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your postgres superuser password")
        print("3. Try running: sc query postgresql-x64-18")
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
    print("1. Update your .env file with the DATABASE_URL above")
    print("2. Restart your BotForm2 server")
    print("3. The application will now connect to the database successfully")
    print("\nTo restart the server:")
    print("  python run.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print("\n✗ UNEXPECTED ERROR: {}".format(str(e)))
        sys.exit(1)

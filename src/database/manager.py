"""
Database Manager for BotForm2

Handles all database operations using psycopg3 with connection pooling.
Follows bobbyofna coding style conventions.
"""

import logging
from typing import Optional, Dict, List, Any
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
import os


class DatabaseManager:
    """Singleton database manager with async connection pooling."""

    _instance = None

    def __init__(self, _connection_string=None):
        """
        Initialize database manager.

        Args:
            _connection_string: PostgreSQL connection string
        """
        self._connection_string = _connection_string
        self._pool = None
        self._logger = logging.getLogger(__name__)

    @classmethod
    def get_instance(cls, _connection_string=None):
        """
        Get singleton instance of DatabaseManager.

        Args:
            _connection_string: PostgreSQL connection string

        Returns:
            DatabaseManager instance
        """
        if cls._instance is None:
            cls._instance = cls(_connection_string=_connection_string)
        return cls._instance

    async def initialize(self):
        """Initialize connection pool and create tables if needed."""
        try:
            # Create async connection pool
            self._pool = AsyncConnectionPool(
                conninfo=self._connection_string,
                min_size=2,
                max_size=10,
                timeout=30
            )

            # Wait for pool to be ready
            await self._pool.wait()

            self._logger.info("Database connection pool initialized")

            # Create tables from schema file
            await self._create_tables()

            return self

        except Exception as e:
            self._logger.error("Failed to initialize database: {}".format(str(e)))
            raise

    async def _create_tables(self):
        """Create database tables from schema.sql if they don't exist."""
        try:
            # Read schema file
            schema_path = os.path.join(
                os.path.dirname(__file__),
                'schema.sql'
            )

            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            # Execute schema
            async with self._pool.connection() as conn:
                await conn.execute(schema_sql)
                await conn.commit()

            self._logger.info("Database tables created successfully")

        except Exception as e:
            self._logger.error("Failed to create tables: {}".format(str(e)))
            raise

    async def close(self):
        """Close database connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._logger.info("Database connection pool closed")

    async def execute(self, _query, _params=None):
        """
        Execute a write query (INSERT, UPDATE, DELETE).

        Args:
            _query: SQL query string
            _params: Query parameters tuple/dict

        Returns:
            Number of affected rows
        """
        try:
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(_query, _params)
                    await conn.commit()
                    return cur.rowcount

        except Exception as e:
            self._logger.error("Execute failed: {}".format(str(e)))
            raise

    async def fetch(self, _query, _params=None):
        """
        Fetch single row from database.

        Args:
            _query: SQL query string
            _params: Query parameters tuple/dict

        Returns:
            Dictionary representing row, or None if no results
        """
        try:
            async with self._pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(_query, _params)
                    result = await cur.fetchone()
                    return result

        except Exception as e:
            self._logger.error("Fetch failed: {}".format(str(e)))
            raise

    async def fetch_all(self, _query, _params=None):
        """
        Fetch all rows from database.

        Args:
            _query: SQL query string
            _params: Query parameters tuple/dict

        Returns:
            List of dictionaries representing rows
        """
        try:
            async with self._pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(_query, _params)
                    results = await cur.fetchall()
                    return results

        except Exception as e:
            self._logger.error("Fetch all failed: {}".format(str(e)))
            raise

    async def create_bot(self, _bot_data):
        """
        Create a new bot record.

        Args:
            _bot_data: Dictionary containing bot configuration

        Returns:
            Created bot record as dictionary
        """
        query = """
            INSERT INTO bots (
                bot_id, name, bot_type, status,
                target_user_url, target_user_address,
                max_trade_value, min_trade_value, copy_ratio,
                stop_loss_percentage, max_daily_loss, notes
            ) VALUES (
                %(bot_id)s, %(name)s, %(bot_type)s, %(status)s,
                %(target_user_url)s, %(target_user_address)s,
                %(max_trade_value)s, %(min_trade_value)s, %(copy_ratio)s,
                %(stop_loss_percentage)s, %(max_daily_loss)s, %(notes)s
            )
            RETURNING *
        """

        result = await self.fetch(query, _bot_data)
        self._logger.info("Created bot: {}".format(_bot_data['bot_id']))
        return result

    async def update_bot(self, _bot_id, _update_data):
        """
        Update bot configuration.

        Args:
            _bot_id: Bot identifier
            _update_data: Dictionary of fields to update

        Returns:
            Updated bot record
        """
        # Build update query dynamically from provided fields
        set_clauses = []
        params = {'bot_id': _bot_id}

        i = 0
        for key, value in _update_data.items():
            set_clauses.append("{} = %({})s".format(key, key))
            params[key] = value
            i = i + 1

        query = """
            UPDATE bots
            SET {}, updated_at = CURRENT_TIMESTAMP
            WHERE bot_id = %(bot_id)s
            RETURNING *
        """.format(', '.join(set_clauses))

        result = await self.fetch(query, params)
        self._logger.info("Updated bot: {}".format(_bot_id))
        return result

    async def get_bot(self, _bot_id):
        """
        Retrieve bot by ID.

        Args:
            _bot_id: Bot identifier

        Returns:
            Bot record as dictionary, or None if not found
        """
        query = "SELECT * FROM bots WHERE bot_id = %(bot_id)s"
        return await self.fetch(query, {'bot_id': _bot_id})

    async def get_all_bots(self, _status=None, _sort_by=None):
        """
        Retrieve all bots with optional filtering and sorting.

        Args:
            _status: Optional status filter ('inactive', 'paper', 'production')
            _sort_by: Optional sort field

        Returns:
            List of bot records
        """
        query = "SELECT * FROM bots"
        params = {}

        if _status is not None:
            query = "{} WHERE status = %(status)s".format(query)
            params['status'] = _status

        if _sort_by is not None:
            query = "{} ORDER BY {}".format(query, _sort_by)
        else:
            query = "{} ORDER BY created_at DESC".format(query)

        return await self.fetch_all(query, params if len(params) > 0 else None)

    async def delete_bot(self, _bot_id):
        """
        Delete bot and all associated records.

        Args:
            _bot_id: Bot identifier

        Returns:
            Number of deleted rows
        """
        query = "DELETE FROM bots WHERE bot_id = %(bot_id)s"
        result = await self.execute(query, {'bot_id': _bot_id})
        self._logger.info("Deleted bot: {}".format(_bot_id))
        return result

    async def record_trade(self, _trade_data):
        """
        Record a new trade.

        Args:
            _trade_data: Dictionary containing trade information

        Returns:
            Created trade record
        """
        query = """
            INSERT INTO trades (
                trade_id, bot_id, is_paper_trade, market_id, outcome,
                amount, price, opened_at, status, source_trade_id, target_trade_id
            ) VALUES (
                %(trade_id)s, %(bot_id)s, %(is_paper_trade)s, %(market_id)s, %(outcome)s,
                %(amount)s, %(price)s, %(opened_at)s, %(status)s, %(source_trade_id)s, %(target_trade_id)s
            )
            RETURNING *
        """

        result = await self.fetch(query, _trade_data)
        self._logger.info("Recorded trade: {}".format(_trade_data['trade_id']))
        return result

    async def update_trade(self, _trade_id, _update_data):
        """
        Update trade record.

        Args:
            _trade_id: Trade identifier
            _update_data: Dictionary of fields to update

        Returns:
            Updated trade record
        """
        set_clauses = []
        params = {'trade_id': _trade_id}

        i = 0
        for key, value in _update_data.items():
            set_clauses.append("{} = %({})s".format(key, key))
            params[key] = value
            i = i + 1

        query = """
            UPDATE trades
            SET {}
            WHERE trade_id = %(trade_id)s
            RETURNING *
        """.format(', '.join(set_clauses))

        result = await self.fetch(query, params)
        return result

    async def get_bot_trades(self, _bot_id, _limit=None, _offset=None, _status=None):
        """
        Retrieve trades for a specific bot.

        Args:
            _bot_id: Bot identifier
            _limit: Maximum number of trades to return
            _offset: Number of trades to skip
            _status: Optional status filter

        Returns:
            List of trade records
        """
        query = "SELECT * FROM trades WHERE bot_id = %(bot_id)s"
        params = {'bot_id': _bot_id}

        if _status is not None:
            query = "{} AND status = %(status)s".format(query)
            params['status'] = _status

        query = "{} ORDER BY opened_at DESC".format(query)

        if _limit is not None:
            query = "{} LIMIT %(limit)s".format(query)
            params['limit'] = _limit

        if _offset is not None:
            query = "{} OFFSET %(offset)s".format(query)
            params['offset'] = _offset

        return await self.fetch_all(query, params)

    async def get_all_trades(self, _limit=None, _offset=None, _status=None):
        """
        Retrieve trades across all bots.

        Args:
            _limit: Maximum number of trades to return
            _offset: Number of trades to skip
            _status: Optional status filter

        Returns:
            List of trade records with bot names
        """
        query = """
            SELECT t.*, b.name as bot_name
            FROM trades t
            LEFT JOIN bots b ON t.bot_id = b.bot_id
            WHERE 1=1
        """
        params = {}

        if _status is not None:
            query = "{} AND t.status = %(status)s".format(query)
            params['status'] = _status

        query = "{} ORDER BY t.opened_at DESC".format(query)

        if _limit is not None:
            query = "{} LIMIT %(limit)s".format(query)
            params['limit'] = _limit

        if _offset is not None:
            query = "{} OFFSET %(offset)s".format(query)
            params['offset'] = _offset

        return await self.fetch_all(query, params)

    async def update_bot_performance(self, _bot_id):
        """
        Update bot performance metrics from trade history.

        Args:
            _bot_id: Bot identifier

        Returns:
            Updated bot record
        """
        # Calculate aggregated performance metrics
        metrics_query = """
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN profit_loss > 0 THEN profit_loss ELSE 0 END) as total_profit,
                SUM(CASE WHEN profit_loss < 0 THEN ABS(profit_loss) ELSE 0 END) as total_loss
            FROM trades
            WHERE bot_id = %(bot_id)s AND status = 'closed'
        """

        metrics = await self.fetch(metrics_query, {'bot_id': _bot_id})

        # Update bot record with metrics
        update_query = """
            UPDATE bots
            SET
                total_trades = %(total_trades)s,
                winning_trades = %(winning_trades)s,
                total_profit = %(total_profit)s,
                total_loss = %(total_loss)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE bot_id = %(bot_id)s
            RETURNING *
        """

        params = {
            'bot_id': _bot_id,
            'total_trades': metrics['total_trades'] if metrics['total_trades'] is not None else 0,
            'winning_trades': metrics['winning_trades'] if metrics['winning_trades'] is not None else 0,
            'total_profit': metrics['total_profit'] if metrics['total_profit'] is not None else 0.0,
            'total_loss': metrics['total_loss'] if metrics['total_loss'] is not None else 0.0
        }

        result = await self.fetch(update_query, params)
        return result

    async def create_performance_snapshot(self, _bot_id, _snapshot_type='hourly'):
        """
        Create a performance snapshot for charting.

        Args:
            _bot_id: Bot identifier
            _snapshot_type: Type of snapshot ('hourly', 'daily', 'weekly')

        Returns:
            Created snapshot record
        """
        # Get current performance
        bot = await self.get_bot(_bot_id)

        if bot is None:
            return None

        total_trades = bot['total_trades'] if bot['total_trades'] is not None else 0
        winning_trades = bot['winning_trades'] if bot['winning_trades'] is not None else 0

        win_rate = 0.0
        if total_trades > 0:
            win_rate = (winning_trades * 100.0) / total_trades
        else:
            win_rate = 0.0

        total_profit = bot['total_profit'] if bot['total_profit'] is not None else 0.0
        total_loss = bot['total_loss'] if bot['total_loss'] is not None else 0.0
        net_profit = total_profit - total_loss

        query = """
            INSERT INTO performance_snapshots (
                bot_id, total_profit, total_trades, win_rate, snapshot_type
            ) VALUES (
                %(bot_id)s, %(total_profit)s, %(total_trades)s, %(win_rate)s, %(snapshot_type)s
            )
            RETURNING *
        """

        params = {
            'bot_id': _bot_id,
            'total_profit': net_profit,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'snapshot_type': _snapshot_type
        }

        result = await self.fetch(query, params)
        return result

    async def get_performance_history(self, _bot_id, _period='24h'):
        """
        Get performance history for charting.

        Args:
            _bot_id: Bot identifier
            _period: Time period ('24h', '1w', '1m', '3m', '1y', 'max')

        Returns:
            List of performance snapshots
        """
        # Map periods to SQL intervals
        interval_map = {
            '24h': '24 hours',
            '1w': '7 days',
            '1m': '30 days',
            '3m': '90 days',
            '1y': '365 days',
            'max': None
        }

        interval = interval_map.get(_period, '24 hours')

        query = "SELECT * FROM performance_snapshots WHERE bot_id = %(bot_id)s"
        params = {'bot_id': _bot_id}

        if interval is not None:
            query = "{} AND timestamp >= NOW() - INTERVAL '{}'".format(query, interval)

        query = "{} ORDER BY timestamp ASC".format(query)

        return await self.fetch_all(query, params)

    async def update_paper_wallet_balance(self, _bot_id, _amount, _operation='subtract'):
        """
        Update paper trading wallet balance.

        Args:
            _bot_id: Bot identifier
            _amount: Amount to add or subtract
            _operation: 'add' or 'subtract'

        Returns:
            Updated bot record with new balance
        """
        if _operation == 'add':
            query = """
                UPDATE bots
                SET paper_wallet_balance = paper_wallet_balance + %(amount)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bot_id = %(bot_id)s
                RETURNING *
            """
        else:
            query = """
                UPDATE bots
                SET paper_wallet_balance = paper_wallet_balance - %(amount)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bot_id = %(bot_id)s
                RETURNING *
            """

        result = await self.fetch(query, {'bot_id': _bot_id, 'amount': _amount})
        self._logger.info("Updated paper wallet for bot {}: {} ${}".format(
            _bot_id, _operation, _amount
        ))
        return result

    async def get_paper_wallet_balance(self, _bot_id):
        """
        Get current paper trading wallet balance.

        Args:
            _bot_id: Bot identifier

        Returns:
            Current balance as float
        """
        query = """
            SELECT paper_wallet_balance
            FROM bots
            WHERE bot_id = %(bot_id)s
        """
        result = await self.fetch(query, {'bot_id': _bot_id})
        if result:
            return float(result['paper_wallet_balance'])
        return None

    async def get_total_paper_wallet_balance(self):
        """
        Get total paper trading wallet balance across all bots.

        Returns:
            Total balance as float
        """
        query = """
            SELECT SUM(paper_wallet_balance) as total_balance
            FROM bots
        """
        result = await self.fetch(query, {})
        if result and result['total_balance'] is not None:
            return float(result['total_balance'])
        return 0.0

    async def reset_paper_wallet(self, _bot_id):
        """
        Reset paper trading wallet to initial balance.

        Args:
            _bot_id: Bot identifier

        Returns:
            Updated bot record
        """
        query = """
            UPDATE bots
            SET paper_wallet_balance = paper_wallet_initial,
                updated_at = CURRENT_TIMESTAMP
            WHERE bot_id = %(bot_id)s
            RETURNING *
        """
        result = await self.fetch(query, {'bot_id': _bot_id})
        self._logger.info("Reset paper wallet for bot: {}".format(_bot_id))
        return result

"""
Copy trading bot implementation for BotForm2.

Copies trades from a target Polymarket user.
Follows bobbyofna coding style conventions.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import re

from .base_bot import BaseBot


class CopyBot(BaseBot):
    """Bot that copies trades from a target user."""

    def __init__(self, _id, _name, _target_url, _target_address=None, _parameters=None, _polymarket_client=None, _db_manager=None):
        """
        Initialize copy bot.

        Args:
            _id: Bot identifier
            _name: Bot name
            _target_url: URL of user to copy (or direct address)
            _target_address: Pre-extracted user address (optional, will extract from URL if not provided)
            _parameters: Bot parameters
            _polymarket_client: Polymarket API client instance
            _db_manager: Database manager instance
        """
        super().__init__(_id=_id, _name=_name, _bot_type='copy', _parameters=_parameters)

        self._target_url = _target_url

        # Use pre-extracted address if provided, otherwise try to extract from URL
        if _target_address is not None:
            self._target_address = _target_address
        else:
            self._target_address = self._extract_user_address(_target_url)

        self._polymarket_client = _polymarket_client
        self._db_manager = _db_manager

        # Track active trades
        self._active_trades = {}
        self._last_check_time = None

        # Track seen transaction hashes to avoid duplicate processing
        self._seen_transactions = set()

    @property
    def target_address(self):
        """Get target user address."""
        return self._target_address

    @property
    def copy_ratio(self):
        """Get copy ratio parameter."""
        return self._parameters.get('copy_ratio', 0.5)

    @property
    def max_trade_value(self):
        """Get maximum trade value."""
        return self._parameters.get('max_trade_value', 500.0)

    @property
    def min_trade_value(self):
        """Get minimum trade value."""
        return self._parameters.get('min_trade_value', 50.0)

    def _extract_user_address(self, _url):
        """
        Extract user address from Polymarket URL.

        Args:
            _url: Polymarket user URL

        Returns:
            Ethereum address
        """
        # Extract address from URL like https://polymarket.com/user/0x1234... or /profile/0x1234...
        match = re.search(r'/(user|profile)/(0x[a-fA-F0-9]+)', _url)
        if match is not None:
            return match.group(2)
        else:
            return None

    async def start(self, _mode='paper'):
        """
        Start bot operation and load active trades.

        Args:
            _mode: Operating mode ('paper' or 'production')

        Returns:
            Self for chaining
        """
        # Call parent start method
        await super().start(_mode)

        # Load active trades from database
        await self._load_active_trades()

        return self

    async def _load_active_trades(self):
        """Load all open trades from database into memory."""
        try:
            if self._db_manager is None:
                return

            # Get all open trades for this bot
            all_trades = await self._db_manager.get_bot_trades(self._id, _limit=1000)

            # Filter for open trades only
            open_count = 0
            for trade in all_trades:
                if trade.get('status') == 'open':
                    trade_id = trade.get('trade_id')
                    self._active_trades[trade_id] = trade
                    open_count = open_count + 1

            self._logger.info("Loaded {} open trades from database".format(open_count))

        except Exception as e:
            self._logger.error("Failed to load active trades: {}".format(str(e)))

    async def _run_loop(self):
        """Main bot execution loop."""
        self._logger.info("Starting copy bot loop for {}".format(self._target_address))

        while self._running == True:
            try:
                await self._poll_user_activity()
                await self._monitor_positions()
                await self._check_daily_loss_limit()
                await asyncio.sleep(5)  # Poll every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Error in run loop: {}".format(str(e)))
                await asyncio.sleep(5)

    async def _poll_user_activity(self):
        """Poll target user for new trades."""
        if self._polymarket_client is None:
            return

        try:
            activities = await self._polymarket_client.get_user_recent_activity(
                _user_address=self._target_address,
                _limit=10
            )

            # Process each activity
            i = 0
            for activity in activities:
                # Check if this is a new trade we haven't seen
                tx_hash = activity.get('transactionHash')

                if tx_hash is None:
                    i = i + 1
                    continue

                # Skip if we've already processed this transaction
                if tx_hash in self._seen_transactions:
                    i = i + 1
                    continue

                # Only process BUY orders (we'll handle SELL separately when monitoring positions)
                side = activity.get('side')
                if side != 'BUY':
                    self._logger.debug("Skipping non-BUY trade: {}".format(side))
                    self._seen_transactions.add(tx_hash)
                    i = i + 1
                    continue

                # Extract trade data
                trade_size = activity.get('size', 0)
                trade_price = activity.get('price', 0)

                # Log the new trade
                self._logger.info("NEW TRADE DETECTED: {} {} @ ${} (tx: {})".format(
                    activity.get('outcome', 'Unknown'),
                    trade_size,
                    trade_price,
                    tx_hash[:10]
                ))

                # Prepare trade data for execution
                trade_data = {
                    'market_id': activity.get('conditionId', ''),
                    'outcome': activity.get('outcome', 'Unknown'),
                    'amount': trade_size,
                    'price': trade_price,
                    'source_trade_id': tx_hash,
                    'target_trade_id': tx_hash,
                    'market_title': activity.get('title', 'Unknown Market'),
                    'market_slug': activity.get('slug', '')
                }

                # Execute the copy trade
                result = await self.execute_trade(trade_data)

                if result is not None:
                    self._logger.info("Successfully copied trade: {}".format(result.get('trade_id')))
                else:
                    self._logger.warning("Failed to copy trade or trade was filtered out")

                # Mark transaction as seen
                self._seen_transactions.add(tx_hash)

                # Limit seen transactions set size to prevent memory issues
                if len(self._seen_transactions) > 1000:
                    # Remove oldest half
                    self._seen_transactions = set(list(self._seen_transactions)[500:])

                i = i + 1

        except Exception as e:
            self._logger.error("Failed to poll user activity: {}".format(str(e)))

    async def _monitor_positions(self):
        """
        Monitor open positions for:
        1. Source trader closing their position (we close ours too)
        2. Stop loss triggers (close if loss > threshold)
        """
        if self._polymarket_client is None:
            return

        if len(self._active_trades) == 0:
            return

        try:
            # Get current market prices for all active positions
            # We need to check if the source trader has closed their positions
            activities = await self._polymarket_client.get_user_recent_activity(
                _user_address=self._target_address,
                _limit=50  # Get more activities to catch SELL orders
            )

            # Build a set of active transaction hashes from recent SELL orders
            source_closed_trades = set()
            for activity in activities:
                if activity.get('side') == 'SELL':
                    source_closed_trades.add(activity.get('transactionHash'))

            # Check each of our active trades
            trades_to_close = []
            for trade_id, trade in list(self._active_trades.items()):
                source_tx = trade.get('source_trade_id')

                # Check if source trader closed this position
                # Note: This is a simplified approach. In reality, we'd need to match
                # the SELL order to the original BUY order by market/outcome/user
                # For now, we'll rely on stop-loss monitoring primarily

                # Check stop loss
                entry_price = float(trade.get('price', 0))
                amount = float(trade.get('amount', 0))
                outcome = trade.get('outcome', '')
                market_id = trade.get('market_id', '')

                # Get current market price
                # For paper trading, we'll simulate by getting recent trades in same market
                current_price = await self._get_current_market_price(market_id, outcome)

                if current_price is None:
                    continue

                # Calculate current P&L percentage
                shares = amount / entry_price if entry_price > 0 else 0
                current_value = shares * current_price
                pnl = current_value - amount
                pnl_percentage = (pnl / amount * 100) if amount > 0 else 0

                # Check stop loss threshold
                stop_loss_pct = float(self._parameters.get('stop_loss_percentage', 10.0))
                if pnl_percentage <= -stop_loss_pct:
                    self._logger.warning(
                        "STOP LOSS TRIGGERED: Trade {} at {:.2f}% loss (threshold: {:.2f}%)".format(
                            trade_id, pnl_percentage, stop_loss_pct
                        )
                    )
                    trades_to_close.append((trade_id, current_price, 'stop_loss'))

            # Close triggered trades
            for trade_id, exit_price, reason in trades_to_close:
                await self.close_trade(trade_id, exit_price)
                self._logger.info("Position closed due to: {}".format(reason))

        except Exception as e:
            self._logger.error("Failed to monitor positions: {}".format(str(e)))

    async def _get_current_market_price(self, _market_id, _outcome):
        """
        Get current market price for a specific outcome.

        Args:
            _market_id: Market/condition ID
            _outcome: Outcome name (e.g., "Yes", "No", "Up", "Down")

        Returns:
            Current price as float, or None if unavailable
        """
        try:
            # Get recent trades for this market from all users
            # Use httpx directly instead of relying on polymarket client's internal client
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as temp_client:
                url = "{}/trades".format(self._polymarket_client._data_url)
                params = {
                    'condition_id': _market_id,
                    '_limit': 5,
                    '_sort': 'timestamp:desc'
                }

                response = await temp_client.get(url, params=params)

                if response.status_code == 200:
                    trades = response.json()

                    # Find most recent trade for this outcome
                    for trade in trades:
                        if trade.get('outcome') == _outcome:
                            return float(trade.get('price', 0))

                # If no recent trades, return None
                return None

        except Exception as e:
            self._logger.debug("Failed to get market price: {}".format(str(e)))
            return None

    async def _check_daily_loss_limit(self):
        """
        Check if bot has exceeded daily loss limit.
        If exceeded, pause the bot temporarily.
        """
        try:
            # Get all closed trades from past 24 hours
            from datetime import timedelta

            max_daily_loss = float(self._parameters.get('max_daily_loss', 1000.0))

            # Query trades from database for past 24 hours
            if self._db_manager is None:
                return

            # Calculate total losses in past 24 hours
            # We'll get all trades and filter in Python for simplicity
            all_trades = await self._db_manager.get_bot_trades(self._id, _limit=100)

            now = datetime.utcnow()
            daily_cutoff = now - timedelta(hours=24)

            total_loss = 0.0
            for trade in all_trades:
                # Only count closed trades
                if trade.get('status') != 'closed':
                    continue

                # Check if within 24 hours
                closed_at = trade.get('closed_at')
                if closed_at is None:
                    continue

                # Parse datetime if it's a string
                if isinstance(closed_at, str):
                    from dateutil import parser
                    closed_at = parser.parse(closed_at)

                if closed_at < daily_cutoff:
                    continue

                # Sum up losses only (negative P&L)
                pnl = float(trade.get('profit_loss', 0))
                if pnl < 0:
                    total_loss = total_loss + abs(pnl)

            # Check if exceeded limit
            if total_loss >= max_daily_loss:
                self._logger.error(
                    "DAILY LOSS LIMIT EXCEEDED: ${:.2f} / ${:.2f} - Pausing bot".format(
                        total_loss, max_daily_loss
                    )
                )
                # Stop the bot
                await self.stop()

                # Update status in database
                await self._db_manager.update_bot(self._id, {
                    'status': 'inactive',
                    'notes': 'Auto-paused: Daily loss limit exceeded (${:.2f})'.format(total_loss)
                })

        except Exception as e:
            self._logger.error("Failed to check daily loss limit: {}".format(str(e)))

    async def execute_trade(self, _trade_data):
        """
        Execute a copy trade with full wallet balance management.

        Args:
            _trade_data: Trade data dictionary containing:
                - market_id: Market identifier
                - outcome: YES/NO
                - amount: Original trade amount
                - price: Entry price (0.0-1.0)
                - source_trade_id: ID of target user's trade
                - target_trade_id: Polymarket trade ID

        Returns:
            Trade result dictionary or None on failure
        """
        # Calculate actual trade amount based on copy ratio
        original_amount = float(_trade_data.get('amount', 0))
        copy_amount = original_amount * float(self.copy_ratio)

        # Apply limits
        if copy_amount < float(self.min_trade_value):
            self._logger.info("Trade amount {} below minimum".format(copy_amount))
            return None

        if copy_amount > float(self.max_trade_value):
            copy_amount = float(self.max_trade_value)
            self._logger.info("Trade amount capped at maximum: {}".format(copy_amount))

        # In paper mode, simulate trade with wallet balance
        if self.is_paper_mode == True:
            return await self._execute_paper_trade(_trade_data, copy_amount)

        # In production mode, execute real trade
        return await self._execute_production_trade(_trade_data, copy_amount)

    async def _execute_paper_trade(self, _trade_data, _amount):
        """
        Execute paper trade with full simulation.

        Args:
            _trade_data: Trade data dictionary
            _amount: Calculated trade amount

        Returns:
            Trade result or None
        """
        try:
            # Check wallet balance
            current_balance = await self._db_manager.get_paper_wallet_balance(self._id)
            if current_balance is None or current_balance < _amount:
                self._logger.warning(
                    "Insufficient paper wallet balance: ${} < ${}".format(
                        current_balance, _amount
                    )
                )
                return None

            # Deduct amount from wallet
            await self._db_manager.update_paper_wallet_balance(
                self._id, _amount, 'subtract'
            )

            # Get market name - prioritize the title from activity data
            # The Polymarket activity feed includes the market title like "Bitcoin Up or Down - January 8, 4AM ET"
            market_name = _trade_data.get('market_title')
            market_id = _trade_data.get('market_id', '')

            # If no title in activity data, try fetching from API
            if not market_name or market_name == 'Unknown Market':
                if market_id and self._polymarket_client is not None:
                    try:
                        market_info = await self._polymarket_client.get_market_info(market_id)
                        if market_info:
                            # Try to get question, title, or description from market API
                            market_name = (
                                market_info.get('question') or
                                market_info.get('title') or
                                market_info.get('description')
                            )
                    except Exception as e:
                        self._logger.debug("Could not fetch market info: {}".format(str(e)))

            # Final fallback
            if not market_name:
                market_name = 'Unknown Market'

            # Record trade in database
            trade_id = "trade_{}".format(datetime.utcnow().timestamp())
            trade_record = {
                'trade_id': trade_id,
                'bot_id': self._id,
                'is_paper_trade': True,
                'market_id': market_id,
                'market_name': market_name,
                'outcome': _trade_data.get('outcome', ''),
                'amount': _amount,
                'price': _trade_data.get('price', 0.0),
                'opened_at': datetime.utcnow(),
                'status': 'open',
                'source_trade_id': _trade_data.get('source_trade_id', ''),
                'target_trade_id': _trade_data.get('target_trade_id', ''),
                'profit_loss': None,
                'exit_price': None,
                'close_value': None
            }

            created_trade = await self._db_manager.record_trade(trade_record)

            # Track in active trades
            self._active_trades[trade_id] = created_trade

            self._logger.info(
                "PAPER TRADE OPENED: ${} {} @ {} (Balance: ${})".format(
                    _amount,
                    _trade_data.get('outcome', ''),
                    _trade_data.get('price', 0),
                    current_balance - _amount
                )
            )

            return {'status': 'open', 'trade_id': trade_id, 'amount': _amount}

        except Exception as e:
            self._logger.error("Paper trade execution failed: {}".format(str(e)))
            return None

    async def _execute_production_trade(self, _trade_data, _amount):
        """
        Execute real production trade.

        Args:
            _trade_data: Trade data dictionary
            _amount: Calculated trade amount

        Returns:
            Trade result
        """
        try:
            result = await self._polymarket_client.place_order(
                _market_id=_trade_data['market_id'],
                _outcome=_trade_data['outcome'],
                _amount=_amount,
                _price=_trade_data['price']
            )
            return result

        except Exception as e:
            self._logger.error("Trade execution failed: {}".format(str(e)))
            return None

    async def close_trade(self, _trade_id, _exit_price):
        """
        Close an open trade and calculate P&L.

        Args:
            _trade_id: Trade identifier
            _exit_price: Exit price (0.0-1.0)

        Returns:
            Closed trade record
        """
        try:
            # CRITICAL: Only close trades that are in our active_trades
            # This prevents closing trades we never opened
            trade = self._active_trades.get(_trade_id)
            if trade is None:
                self._logger.warning(
                    "Attempted to close trade {} that is not in active trades. "
                    "This may indicate the bot is trying to close a position it never opened.".format(_trade_id)
                )
                return None

            # Verify this trade actually belongs to this bot
            if trade.get('bot_id') != self._id:
                self._logger.error(
                    "Trade {} belongs to bot {} but close was called by bot {}. Rejecting.".format(
                        _trade_id, trade.get('bot_id'), self._id
                    )
                )
                return None

            # Double-check database status for consistency
            db_trade = await self._db_manager.get_bot_trades(
                self._id, _limit=1000, _status='open'
            )
            trade_exists_in_db = any(t['trade_id'] == _trade_id for t in db_trade)

            if not trade_exists_in_db:
                self._logger.error(
                    "Trade {} is in active_trades but not found as open in database. "
                    "Removing from active_trades to maintain consistency.".format(_trade_id)
                )
                del self._active_trades[_trade_id]
                return None

            # Validate exit price (must be between 0.0 and 1.0 for prediction markets)
            if _exit_price <= 0.0 or _exit_price > 1.0:
                self._logger.error(
                    "Invalid exit price {} for trade {}. Must be between 0.0 and 1.0".format(
                        _exit_price, _trade_id
                    )
                )
                return None

            # Calculate P&L
            entry_price = float(trade['price'])
            amount = float(trade['amount'])

            # P&L = amount * (exit_price - entry_price)
            # If you bought YES at 0.60 for $100, you get 100/0.60 = 166.67 shares
            # If price goes to 0.70, shares are worth 166.67 * 0.70 = $116.67
            # Profit = $116.67 - $100 = $16.67
            shares = amount / entry_price
            exit_value = shares * _exit_price
            profit_loss = exit_value - amount

            # Update trade in database
            update_data = {
                'status': 'closed',
                'closed_at': datetime.utcnow(),
                'exit_price': _exit_price,
                'close_value': exit_value,
                'profit_loss': profit_loss
            }

            closed_trade = await self._db_manager.update_trade(_trade_id, update_data)

            # Return funds to wallet (original amount + profit/loss)
            total_return = amount + profit_loss
            if total_return > 0:
                await self._db_manager.update_paper_wallet_balance(
                    self._id, total_return, 'add'
                )

            # Update bot performance
            await self._db_manager.update_bot_performance(self._id)

            # Remove from active trades
            del self._active_trades[_trade_id]

            self._logger.info(
                "TRADE CLOSED: {} - P&L: ${:.2f} (Entry: {} Exit: {})".format(
                    _trade_id, profit_loss, entry_price, _exit_price
                )
            )

            return closed_trade

        except Exception as e:
            self._logger.error("Failed to close trade: {}".format(str(e)))
            return None

    def calculate_unrealized_pnl(self, _trade_id, _current_price):
        """
        Calculate unrealized P&L for an open trade.

        Args:
            _trade_id: Trade identifier
            _current_price: Current market price (0.0-1.0)

        Returns:
            Unrealized P&L as float
        """
        trade = self._active_trades.get(_trade_id)
        if trade is None:
            return 0.0

        entry_price = float(trade['price'])
        amount = float(trade['amount'])

        shares = amount / entry_price
        current_value = shares * _current_price
        unrealized_pnl = current_value - amount

        return unrealized_pnl

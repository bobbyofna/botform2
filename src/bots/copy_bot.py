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

    def __init__(self, _id, _name, _target_url, _parameters=None, _polymarket_client=None, _db_manager=None):
        """
        Initialize copy bot.

        Args:
            _id: Bot identifier
            _name: Bot name
            _target_url: URL of user to copy
            _parameters: Bot parameters
            _polymarket_client: Polymarket API client instance
            _db_manager: Database manager instance
        """
        super().__init__(_id=_id, _name=_name, _bot_type='copy', _parameters=_parameters)

        self._target_url = _target_url
        self._target_address = self._extract_user_address(_target_url)
        self._polymarket_client = _polymarket_client
        self._db_manager = _db_manager

        # Track active trades
        self._active_trades = {}
        self._last_check_time = None

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

    async def _run_loop(self):
        """Main bot execution loop."""
        self._logger.info("Starting copy bot loop for {}".format(self._target_address))

        while self._running == True:
            try:
                await self._poll_user_activity()
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
                # Log trade activity
                self._logger.info("Trade activity {}: {}".format(i, activity))
                i = i + 1

        except Exception as e:
            self._logger.error("Failed to poll user activity: {}".format(str(e)))

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
        original_amount = _trade_data.get('amount', 0)
        copy_amount = original_amount * self.copy_ratio

        # Apply limits
        if copy_amount < self.min_trade_value:
            self._logger.info("Trade amount {} below minimum".format(copy_amount))
            return None

        if copy_amount > self.max_trade_value:
            copy_amount = self.max_trade_value
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

            # Record trade in database
            trade_id = "trade_{}".format(datetime.utcnow().timestamp())
            trade_record = {
                'trade_id': trade_id,
                'bot_id': self._id,
                'is_paper_trade': True,
                'market_id': _trade_data.get('market_id', ''),
                'outcome': _trade_data.get('outcome', ''),
                'amount': _amount,
                'price': _trade_data.get('price', 0.0),
                'opened_at': datetime.utcnow(),
                'status': 'open',
                'source_trade_id': _trade_data.get('source_trade_id', ''),
                'target_trade_id': _trade_data.get('target_trade_id', ''),
                'profit_loss': None,
                'exit_price': None
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
            # Get trade from database
            trade = self._active_trades.get(_trade_id)
            if trade is None:
                self._logger.error("Trade {} not found in active trades".format(_trade_id))
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

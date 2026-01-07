"""
Bot manager for BotForm2.

Manages bot lifecycle and task scheduling.
Follows bobbyofna coding style conventions.
"""

import logging
import asyncio
from typing import Dict, Optional

from .copy_bot import CopyBot


class BotManager:
    """Manages all bot instances and their lifecycle."""

    def __init__(self, _polymarket_client=None, _db_manager=None):
        """
        Initialize bot manager.

        Args:
            _polymarket_client: Polymarket API client instance
            _db_manager: Database manager instance
        """
        self._polymarket_client = _polymarket_client
        self._db_manager = _db_manager
        self._active_bots = {}
        self._logger = logging.getLogger(__name__)

    @property
    def active_bots(self):
        """Get dictionary of active bots."""
        return self._active_bots

    @property
    def bot_count(self):
        """Get number of active bots."""
        return len(self._active_bots)

    def get_bot(self, _bot_id):
        """
        Get bot instance by ID.

        Args:
            _bot_id: Bot identifier

        Returns:
            Bot instance or None
        """
        return self._active_bots.get(_bot_id, None)

    async def create_bot(self, _bot_data):
        """
        Create a new bot instance.

        Args:
            _bot_data: Dictionary containing bot configuration

        Returns:
            Created bot instance
        """
        bot_id = _bot_data['bot_id']
        bot_type = _bot_data['bot_type']

        if bot_type == 'copy':
            bot = CopyBot(
                _id=bot_id,
                _name=_bot_data['name'],
                _target_url=_bot_data['target_user_url'],
                _parameters={
                    'max_trade_value': _bot_data.get('max_trade_value', 500.0),
                    'min_trade_value': _bot_data.get('min_trade_value', 50.0),
                    'copy_ratio': _bot_data.get('copy_ratio', 0.5),
                    'stop_loss_percentage': _bot_data.get('stop_loss_percentage', 10.0),
                    'max_daily_loss': _bot_data.get('max_daily_loss', 1000.0)
                },
                _polymarket_client=self._polymarket_client,
                _db_manager=self._db_manager
            )

            self._active_bots[bot_id] = bot
            self._logger.info("Created bot: {}".format(bot_id))
            return bot

        else:
            raise ValueError("Unknown bot type: {}".format(bot_type))

    async def start_bot(self, _bot_id, _mode='paper'):
        """
        Start a bot.

        Args:
            _bot_id: Bot identifier
            _mode: Operating mode ('paper' or 'production')

        Returns:
            Bot instance
        """
        bot = self.get_bot(_bot_id)

        if bot is None:
            raise ValueError("Bot not found: {}".format(_bot_id))

        await bot.start(_mode=_mode)
        self._logger.info("Started bot {} in {} mode".format(_bot_id, _mode))
        return bot

    async def stop_bot(self, _bot_id):
        """
        Stop a bot.

        Args:
            _bot_id: Bot identifier

        Returns:
            Bot instance
        """
        bot = self.get_bot(_bot_id)

        if bot is None:
            raise ValueError("Bot not found: {}".format(_bot_id))

        await bot.stop()
        self._logger.info("Stopped bot: {}".format(_bot_id))
        return bot

    async def remove_bot(self, _bot_id):
        """
        Remove a bot from manager.

        Args:
            _bot_id: Bot identifier

        Returns:
            True if removed, False if not found
        """
        bot = self.get_bot(_bot_id)

        if bot is None:
            return False

        # Stop bot if running
        if bot.is_running == True:
            await bot.stop()

        # Remove from active bots
        del self._active_bots[_bot_id]
        self._logger.info("Removed bot: {}".format(_bot_id))
        return True

    async def cleanup(self):
        """Stop all bots and cleanup resources."""
        self._logger.info("Cleaning up bot manager")

        bot_ids = list(self._active_bots.keys())
        i = 0
        for bot_id in bot_ids:
            try:
                await self.stop_bot(bot_id)
            except Exception as e:
                self._logger.error("Error stopping bot {}: {}".format(bot_id, str(e)))
            i = i + 1

        self._active_bots.clear()
        self._logger.info("Bot manager cleanup complete")

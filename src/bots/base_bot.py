"""
Base bot abstract class for BotForm2.

Foundation for all bot types.
Follows bobbyofna coding style conventions.
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class BaseBot(ABC):
    """Abstract base class for all trading bots."""

    def __init__(self, _id, _name, _bot_type, _parameters=None):
        """
        Initialize base bot.

        Args:
            _id: Unique bot identifier
            _name: Human-readable name
            _bot_type: Bot type identifier
            _parameters: Dictionary of bot parameters
        """
        self._id = _id
        self._name = _name
        self._bot_type = _bot_type
        self._parameters = {} if _parameters is None else _parameters
        self._status = 'inactive'
        self._running = False
        self._task = None
        self._logger = logging.getLogger("{}.{}".format(__name__, _id))

    @property
    def id(self):
        """Get bot ID."""
        return self._id

    @property
    def name(self):
        """Get bot name."""
        return self._name

    @property
    def bot_type(self):
        """Get bot type."""
        return self._bot_type

    @property
    def status(self):
        """Get bot status."""
        return self._status

    @property
    def is_running(self):
        """Check if bot is currently running."""
        return True if self._running == True else False

    @property
    def is_paper_mode(self):
        """Check if bot is in paper trading mode."""
        return True if self._status == 'paper' else False

    @property
    def parameters(self):
        """Get bot parameters."""
        return self._parameters

    async def start(self, _mode='paper'):
        """
        Start bot operation.

        Args:
            _mode: Operating mode ('paper' or 'production')

        Returns:
            Self for chaining
        """
        if self.is_running == True:
            self._logger.warning("Bot already running")
            return self

        self._status = _mode
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        self._logger.info("Bot started in {} mode".format(_mode))

        return self

    async def stop(self):
        """
        Stop bot operation.

        Returns:
            Self for chaining
        """
        if self.is_running == False:
            self._logger.warning("Bot not running")
            return self

        self._running = False
        self._status = 'inactive'

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._logger.info("Bot stopped")
        return self

    async def update_parameters(self, _parameters):
        """
        Update bot parameters.

        Args:
            _parameters: Dictionary of parameters to update

        Returns:
            Self for chaining
        """
        self._parameters.update(_parameters)
        self._logger.info("Parameters updated")
        return self

    @abstractmethod
    async def _run_loop(self):
        """Main bot execution loop - must be implemented by subclasses."""
        pass

    @abstractmethod
    async def execute_trade(self, _trade_data):
        """Execute a trade - must be implemented by subclasses."""
        pass

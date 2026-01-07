"""
Bot data model for BotForm2.

Represents bot configuration and state.
Follows bobbyofna coding style conventions.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class Bot:
    """Bot configuration and state model."""

    def __init__(self, _bot_id, _name, _bot_type, _status='inactive', _parameters=None):
        """
        Initialize bot model.

        Args:
            _bot_id: Unique bot identifier
            _name: Human-readable bot name
            _bot_type: Type of bot ('copy')
            _status: Current status ('inactive', 'paper', 'production')
            _parameters: Dictionary of bot parameters
        """
        self._bot_id = _bot_id
        self._name = _name
        self._bot_type = _bot_type
        self._status = _status
        self._parameters = {} if _parameters is None else _parameters

        # Timestamps
        self._created_at = None
        self._updated_at = None

        # Copy bot specific fields
        self._target_user_url = None
        self._target_user_address = None

        # Performance metrics
        self._total_trades = 0
        self._winning_trades = 0
        self._total_profit = 0.0
        self._total_loss = 0.0

        # Notes
        self._notes = ''

    @property
    def bot_id(self):
        """Get bot ID."""
        return self._bot_id

    @property
    def name(self):
        """Get bot name."""
        return self._name

    @name.setter
    def name(self, _value):
        """Set bot name."""
        self._name = _value

    @property
    def bot_type(self):
        """Get bot type."""
        return self._bot_type

    @property
    def status(self):
        """Get bot status."""
        return self._status

    @status.setter
    def status(self, _value):
        """Set bot status."""
        self._status = _value

    @property
    def parameters(self):
        """Get bot parameters."""
        return self._parameters

    @property
    def target_user_url(self):
        """Get target user URL."""
        return self._target_user_url

    @target_user_url.setter
    def target_user_url(self, _value):
        """Set target user URL."""
        self._target_user_url = _value

    @property
    def target_user_address(self):
        """Get target user address."""
        return self._target_user_address

    @target_user_address.setter
    def target_user_address(self, _value):
        """Set target user address."""
        self._target_user_address = _value

    @property
    def max_trade_value(self):
        """Get maximum trade value."""
        return self._parameters.get('max_trade_value', 500.0)

    @property
    def min_trade_value(self):
        """Get minimum trade value."""
        return self._parameters.get('min_trade_value', 50.0)

    @property
    def copy_ratio(self):
        """Get copy ratio."""
        return self._parameters.get('copy_ratio', 0.5)

    @property
    def stop_loss_percentage(self):
        """Get stop loss percentage."""
        return self._parameters.get('stop_loss_percentage', 10.0)

    @property
    def max_daily_loss(self):
        """Get maximum daily loss."""
        return self._parameters.get('max_daily_loss', 1000.0)

    @property
    def total_trades(self):
        """Get total number of trades."""
        return self._total_trades

    @property
    def winning_trades(self):
        """Get number of winning trades."""
        return self._winning_trades

    @property
    def total_profit(self):
        """Get total profit."""
        return self._total_profit

    @property
    def total_loss(self):
        """Get total loss."""
        return self._total_loss

    @property
    def net_profit(self):
        """Calculate net profit."""
        return self._total_profit - self._total_loss

    @property
    def win_rate(self):
        """Calculate win rate as percentage."""
        if self._total_trades > 0:
            return (self._winning_trades * 100.0) / self._total_trades
        else:
            return 0.0

    @property
    def notes(self):
        """Get notes."""
        return self._notes

    @notes.setter
    def notes(self, _value):
        """Set notes."""
        self._notes = _value

    @property
    def is_active(self):
        """Check if bot is currently running."""
        return True if self._status in ['paper', 'production'] else False

    @property
    def is_paper_mode(self):
        """Check if bot is in paper trading mode."""
        return True if self._status == 'paper' else False

    @property
    def is_production_mode(self):
        """Check if bot is in production mode."""
        return True if self._status == 'production' else False

    def to_dict(self):
        """
        Convert bot to dictionary representation.

        Returns:
            Dictionary containing all bot data
        """
        return {
            'bot_id': self._bot_id,
            'name': self._name,
            'bot_type': self._bot_type,
            'status': self._status,
            'target_user_url': self._target_user_url,
            'target_user_address': self._target_user_address,
            'max_trade_value': self.max_trade_value,
            'min_trade_value': self.min_trade_value,
            'copy_ratio': self.copy_ratio,
            'stop_loss_percentage': self.stop_loss_percentage,
            'max_daily_loss': self.max_daily_loss,
            'notes': self._notes,
            'total_trades': self._total_trades,
            'winning_trades': self._winning_trades,
            'total_profit': self._total_profit,
            'total_loss': self._total_loss,
            'net_profit': self.net_profit,
            'win_rate': self.win_rate,
            'created_at': self._created_at.isoformat() if self._created_at is not None else None,
            'updated_at': self._updated_at.isoformat() if self._updated_at is not None else None
        }

    @classmethod
    def from_dict(cls, _data):
        """
        Create bot instance from dictionary.

        Args:
            _data: Dictionary containing bot data

        Returns:
            Bot instance
        """
        bot = cls(
            _bot_id=_data['bot_id'],
            _name=_data['name'],
            _bot_type=_data['bot_type'],
            _status=_data.get('status', 'inactive')
        )

        # Set additional fields
        bot._target_user_url = _data.get('target_user_url', None)
        bot._target_user_address = _data.get('target_user_address', None)

        # Set parameters
        bot._parameters = {
            'max_trade_value': _data.get('max_trade_value', 500.0),
            'min_trade_value': _data.get('min_trade_value', 50.0),
            'copy_ratio': _data.get('copy_ratio', 0.5),
            'stop_loss_percentage': _data.get('stop_loss_percentage', 10.0),
            'max_daily_loss': _data.get('max_daily_loss', 1000.0)
        }

        # Set performance metrics
        bot._total_trades = _data.get('total_trades', 0)
        bot._winning_trades = _data.get('winning_trades', 0)
        bot._total_profit = float(_data.get('total_profit', 0.0))
        bot._total_loss = float(_data.get('total_loss', 0.0))

        # Set notes
        bot._notes = _data.get('notes', '')

        # Set timestamps
        bot._created_at = _data.get('created_at', None)
        bot._updated_at = _data.get('updated_at', None)

        return bot

"""
Performance data model for BotForm2.

Represents performance snapshots for charting.
Follows bobbyofna coding style conventions.
"""

from typing import Optional
from datetime import datetime


class PerformanceSnapshot:
    """Performance snapshot model for time-series data."""

    def __init__(self, _bot_id, _total_profit, _total_trades, _win_rate, _snapshot_type='hourly'):
        """
        Initialize performance snapshot.

        Args:
            _bot_id: Bot identifier
            _total_profit: Total net profit at snapshot time
            _total_trades: Total number of trades
            _win_rate: Win rate percentage
            _snapshot_type: Type of snapshot ('hourly', 'daily', 'weekly')
        """
        self._bot_id = _bot_id
        self._total_profit = _total_profit
        self._total_trades = _total_trades
        _win_rate = _win_rate
        self._snapshot_type = _snapshot_type
        self._timestamp = None
        self._id = None

    @property
    def bot_id(self):
        """Get bot ID."""
        return self._bot_id

    @property
    def total_profit(self):
        """Get total profit."""
        return self._total_profit

    @property
    def total_trades(self):
        """Get total trades."""
        return self._total_trades

    @property
    def win_rate(self):
        """Get win rate."""
        return self._win_rate

    @property
    def snapshot_type(self):
        """Get snapshot type."""
        return self._snapshot_type

    @property
    def timestamp(self):
        """Get timestamp."""
        return self._timestamp

    @timestamp.setter
    def timestamp(self, _value):
        """Set timestamp."""
        self._timestamp = _value

    def to_dict(self):
        """
        Convert performance snapshot to dictionary.

        Returns:
            Dictionary containing snapshot data
        """
        return {
            'bot_id': self._bot_id,
            'total_profit': float(self._total_profit),
            'total_trades': self._total_trades,
            'win_rate': float(self._win_rate),
            'snapshot_type': self._snapshot_type,
            'timestamp': self._timestamp.isoformat() if self._timestamp is not None else None
        }

    @classmethod
    def from_dict(cls, _data):
        """
        Create performance snapshot from dictionary.

        Args:
            _data: Dictionary containing snapshot data

        Returns:
            PerformanceSnapshot instance
        """
        snapshot = cls(
            _bot_id=_data['bot_id'],
            _total_profit=float(_data['total_profit']),
            _total_trades=_data['total_trades'],
            _win_rate=float(_data['win_rate']),
            _snapshot_type=_data.get('snapshot_type', 'hourly')
        )

        snapshot._timestamp = _data.get('timestamp', None)
        snapshot._id = _data.get('id', None)

        return snapshot

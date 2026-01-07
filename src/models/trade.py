"""
Trade data model for BotForm2.

Represents individual trade records.
Follows bobbyofna coding style conventions.
"""

from typing import Optional
from datetime import datetime


class Trade:
    """Trade record model."""

    def __init__(self, _trade_id, _bot_id, _is_paper_trade, _market_id, _outcome, _amount, _price):
        """
        Initialize trade model.

        Args:
            _trade_id: Unique trade identifier
            _bot_id: ID of bot that made the trade
            _is_paper_trade: Whether this is a paper trade
            _market_id: Polymarket market ID
            _outcome: Outcome being traded ('YES' or 'NO')
            _amount: Trade amount in dollars
            _price: Trade price (probability)
        """
        self._trade_id = _trade_id
        self._bot_id = _bot_id
        self._is_paper_trade = _is_paper_trade
        self._market_id = _market_id
        self._outcome = _outcome
        self._amount = _amount
        self._price = _price

        # Timestamps
        self._opened_at = None
        self._closed_at = None

        # Results
        self._profit_loss = None
        self._status = 'open'

        # Copy trading links
        self._source_trade_id = None
        self._target_trade_id = None

    @property
    def trade_id(self):
        """Get trade ID."""
        return self._trade_id

    @property
    def bot_id(self):
        """Get bot ID."""
        return self._bot_id

    @property
    def is_paper_trade(self):
        """Check if this is a paper trade."""
        return True if self._is_paper_trade == True else False

    @property
    def market_id(self):
        """Get market ID."""
        return self._market_id

    @property
    def outcome(self):
        """Get outcome."""
        return self._outcome

    @property
    def amount(self):
        """Get trade amount."""
        return self._amount

    @property
    def price(self):
        """Get trade price."""
        return self._price

    @property
    def opened_at(self):
        """Get opened timestamp."""
        return self._opened_at

    @opened_at.setter
    def opened_at(self, _value):
        """Set opened timestamp."""
        self._opened_at = _value

    @property
    def closed_at(self):
        """Get closed timestamp."""
        return self._closed_at

    @closed_at.setter
    def closed_at(self, _value):
        """Set closed timestamp."""
        self._closed_at = _value

    @property
    def profit_loss(self):
        """Get profit/loss amount."""
        return self._profit_loss

    @profit_loss.setter
    def profit_loss(self, _value):
        """Set profit/loss amount."""
        self._profit_loss = _value

    @property
    def status(self):
        """Get trade status."""
        return self._status

    @status.setter
    def status(self, _value):
        """Set trade status."""
        self._status = _value

    @property
    def source_trade_id(self):
        """Get source trade ID."""
        return self._source_trade_id

    @source_trade_id.setter
    def source_trade_id(self, _value):
        """Set source trade ID."""
        self._source_trade_id = _value

    @property
    def target_trade_id(self):
        """Get target trade ID."""
        return self._target_trade_id

    @target_trade_id.setter
    def target_trade_id(self, _value):
        """Set target trade ID."""
        self._target_trade_id = _value

    @property
    def is_open(self):
        """Check if trade is currently open."""
        return True if self._status == 'open' else False

    @property
    def is_closed(self):
        """Check if trade is closed."""
        return True if self._status == 'closed' else False

    @property
    def is_cancelled(self):
        """Check if trade is cancelled."""
        return True if self._status == 'cancelled' else False

    @property
    def is_profitable(self):
        """Check if trade was profitable."""
        if self._profit_loss is not None:
            return True if self._profit_loss > 0 else False
        else:
            return False

    @property
    def duration(self):
        """Calculate trade duration in seconds."""
        if self._opened_at is not None and self._closed_at is not None:
            delta = self._closed_at - self._opened_at
            return delta.total_seconds()
        else:
            return None

    def to_dict(self):
        """
        Convert trade to dictionary representation.

        Returns:
            Dictionary containing all trade data
        """
        return {
            'trade_id': self._trade_id,
            'bot_id': self._bot_id,
            'is_paper_trade': self._is_paper_trade,
            'market_id': self._market_id,
            'outcome': self._outcome,
            'amount': float(self._amount),
            'price': float(self._price),
            'opened_at': self._opened_at.isoformat() if self._opened_at is not None else None,
            'closed_at': self._closed_at.isoformat() if self._closed_at is not None else None,
            'profit_loss': float(self._profit_loss) if self._profit_loss is not None else None,
            'status': self._status,
            'source_trade_id': self._source_trade_id,
            'target_trade_id': self._target_trade_id
        }

    @classmethod
    def from_dict(cls, _data):
        """
        Create trade instance from dictionary.

        Args:
            _data: Dictionary containing trade data

        Returns:
            Trade instance
        """
        trade = cls(
            _trade_id=_data['trade_id'],
            _bot_id=_data['bot_id'],
            _is_paper_trade=_data['is_paper_trade'],
            _market_id=_data['market_id'],
            _outcome=_data['outcome'],
            _amount=float(_data['amount']),
            _price=float(_data['price'])
        )

        # Set timestamps
        trade._opened_at = _data.get('opened_at', None)
        trade._closed_at = _data.get('closed_at', None)

        # Set results
        if _data.get('profit_loss', None) is not None:
            trade._profit_loss = float(_data['profit_loss'])
        else:
            trade._profit_loss = None

        trade._status = _data.get('status', 'open')

        # Set copy trading links
        trade._source_trade_id = _data.get('source_trade_id', None)
        trade._target_trade_id = _data.get('target_trade_id', None)

        return trade

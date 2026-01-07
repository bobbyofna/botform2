"""
ID generation utility for BotForm2.

Generates unique 7-digit IDs for bots and trades.
Follows bobbyofna coding style conventions.
"""

import random
from typing import Set, Optional


class IDGenerator:
    """Generates unique 7-digit integer IDs."""

    def __init__(self):
        """Initialize ID generator."""
        self._used_ids = set()
        self._min_id = 1000000
        self._max_id = 9999999

    @property
    def used_ids(self):
        """Get set of used IDs."""
        return self._used_ids

    def register_id(self, _id):
        """
        Register an existing ID as used.

        Args:
            _id: ID to register

        Returns:
            Self for chaining
        """
        self._used_ids.add(_id)
        return self

    def generate(self, _prefix=''):
        """
        Generate a unique 7-digit ID.

        Args:
            _prefix: Optional prefix for ID (e.g., 'BOT', 'TRD')

        Returns:
            Unique ID string
        """
        max_attempts = 100
        attempts = 0

        while attempts < max_attempts:
            # Generate random 7-digit number
            id_number = random.randint(self._min_id, self._max_id)

            # Create full ID with prefix
            if _prefix != '':
                full_id = "{}{}".format(_prefix, id_number)
            else:
                full_id = str(id_number)

            # Check if ID is unique
            if full_id not in self._used_ids:
                self._used_ids.add(full_id)
                return full_id

            attempts = attempts + 1

        # If we couldn't generate unique ID after max attempts
        raise Exception("Could not generate unique ID after {} attempts".format(max_attempts))

    def generate_bot_id(self):
        """
        Generate unique bot ID with BOT prefix.

        Returns:
            Unique bot ID string (e.g., 'BOT1234567')
        """
        return self.generate(_prefix='BOT')

    def generate_trade_id(self):
        """
        Generate unique trade ID with TRD prefix.

        Returns:
            Unique trade ID string (e.g., 'TRD1234567')
        """
        return self.generate(_prefix='TRD')

    def clear_used_ids(self):
        """
        Clear all registered IDs.

        Returns:
            Self for chaining
        """
        self._used_ids.clear()
        return self


# Global ID generator instance
id_generator = IDGenerator()

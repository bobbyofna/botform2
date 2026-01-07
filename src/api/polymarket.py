"""
Polymarket API client for BotForm2.

Handles all interactions with the Polymarket API.
Follows bobbyofna coding style conventions.
"""

import logging
import asyncio
from typing import Optional, Dict, List, Any
import httpx
from datetime import datetime


class PolymarketClient:
    """Async HTTP client for Polymarket API."""

    def __init__(self, _api_key='', _api_secret='', _base_url='https://api.polymarket.com'):
        """
        Initialize Polymarket client.

        Args:
            _api_key: Polymarket API key
            _api_secret: Polymarket API secret
            _base_url: Base URL for Polymarket API
        """
        self._api_key = _api_key
        self._api_secret = _api_secret
        self._base_url = _base_url
        self._client = None
        self._logger = logging.getLogger(__name__)

        # Rate limiting
        self._rate_limit_delay = 0.2  # 200ms minimum delay
        self._last_request_time = None
        self._backoff_time = 1.0  # Initial backoff time for 429 errors

    @property
    def base_url(self):
        """Get base URL."""
        return self._base_url

    async def initialize(self):
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers={
                'User-Agent': 'BotForm2/1.0'
            }
        )
        self._logger.info("Polymarket client initialized")
        return self

    async def close(self):
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._logger.info("Polymarket client closed")

    async def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self._last_request_time is not None:
            elapsed = datetime.now().timestamp() - self._last_request_time
            if elapsed < self._rate_limit_delay:
                wait_time = self._rate_limit_delay - elapsed
                await asyncio.sleep(wait_time)

        self._last_request_time = datetime.now().timestamp()

    async def _request(self, _method, _endpoint, _params=None, _data=None):
        """
        Make HTTP request with rate limiting and error handling.

        Args:
            _method: HTTP method ('GET', 'POST', etc.)
            _endpoint: API endpoint
            _params: Query parameters
            _data: Request body data

        Returns:
            Response JSON data
        """
        await self._wait_for_rate_limit()

        try:
            response = await self._client.request(
                method=_method,
                url=_endpoint,
                params=_params,
                json=_data
            )

            # Handle rate limiting
            if response.status_code == 429:
                self._logger.warning("Rate limit hit, backing off for {}s".format(self._backoff_time))
                await asyncio.sleep(self._backoff_time)
                self._backoff_time = self._backoff_time * 2  # Exponential backoff
                return await self._request(_method, _endpoint, _params, _data)

            # Reset backoff on success
            if response.status_code == 200:
                self._backoff_time = 1.0

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            self._logger.error("HTTP error {}: {}".format(e.response.status_code, str(e)))
            raise
        except Exception as e:
            self._logger.error("Request failed: {}".format(str(e)))
            raise

    async def get_user_activity(self, _user_address, _limit=50):
        """
        Get recent activity for a user.

        Args:
            _user_address: Ethereum address of user
            _limit: Maximum number of activities to return

        Returns:
            List of user activities
        """
        endpoint = "/users/{}/activity".format(_user_address)
        params = {'limit': _limit}

        try:
            data = await self._request('GET', endpoint, _params=params)
            return data
        except Exception as e:
            self._logger.error("Failed to get user activity: {}".format(str(e)))
            return []

    async def get_market_info(self, _market_id):
        """
        Get information about a market.

        Args:
            _market_id: Market identifier

        Returns:
            Market information dictionary
        """
        endpoint = "/markets/{}".format(_market_id)

        try:
            data = await self._request('GET', endpoint)
            return data
        except Exception as e:
            self._logger.error("Failed to get market info: {}".format(str(e)))
            return None

    async def place_order(self, _market_id, _outcome, _amount, _price):
        """
        Place an order on Polymarket.

        Args:
            _market_id: Market identifier
            _outcome: Outcome to trade ('YES' or 'NO')
            _amount: Amount in dollars
            _price: Price (probability between 0 and 1)

        Returns:
            Order response dictionary
        """
        endpoint = "/orders"
        data = {
            'market_id': _market_id,
            'outcome': _outcome,
            'amount': float(_amount),
            'price': float(_price)
        }

        try:
            response = await self._request('POST', endpoint, _data=data)
            self._logger.info("Order placed: market={}, outcome={}, amount={}".format(
                _market_id, _outcome, _amount
            ))
            return response
        except Exception as e:
            self._logger.error("Failed to place order: {}".format(str(e)))
            raise

    async def cancel_order(self, _order_id):
        """
        Cancel an existing order.

        Args:
            _order_id: Order identifier

        Returns:
            Cancellation response
        """
        endpoint = "/orders/{}".format(_order_id)

        try:
            response = await self._request('DELETE', endpoint)
            self._logger.info("Order cancelled: {}".format(_order_id))
            return response
        except Exception as e:
            self._logger.error("Failed to cancel order: {}".format(str(e)))
            raise

    async def get_positions(self, _user_address=None):
        """
        Get current open positions.

        Args:
            _user_address: Optional user address (uses authenticated user if None)

        Returns:
            List of positions
        """
        if _user_address is not None:
            endpoint = "/users/{}/positions".format(_user_address)
        else:
            endpoint = "/positions"

        try:
            data = await self._request('GET', endpoint)
            return data
        except Exception as e:
            self._logger.error("Failed to get positions: {}".format(str(e)))
            return []

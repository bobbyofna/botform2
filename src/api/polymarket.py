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
            _base_url: Base URL for Polymarket API (legacy)
        """
        self._api_key = _api_key
        self._api_secret = _api_secret
        self._base_url = _base_url

        # Polymarket has 4 primary API services
        self._clob_url = 'https://clob.polymarket.com'  # Central Limit Order Book
        self._gamma_url = 'https://gamma-api.polymarket.com'  # Market data
        self._strapi_url = 'https://strapi-matic.poly.market'  # Alternative endpoint
        self._data_url = 'https://data-api.polymarket.com'  # Data API

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

    async def validate_user_address(self, _user_address):
        """
        Validate that a user address exists and can be accessed.
        Tries to fetch user activity to verify the address is valid.

        Args:
            _user_address: Ethereum address to validate

        Returns:
            Dictionary with 'valid' (bool) and 'message' (str)
        """
        try:
            # Basic address format validation
            import re
            if re.match(r'^0x[a-fA-F0-9]{40}$', _user_address) is None:
                return {
                    'valid': False,
                    'message': 'Invalid Ethereum address format'
                }

            # Try to validate with Polymarket API
            try:
                # Create a separate client for this request to use correct base URL
                async with httpx.AsyncClient(timeout=10.0) as temp_client:
                    # Try Strapi API for user activity (most reliable for user data)
                    url = "{}/api/users".format(self._strapi_url)
                    params = {'filters[address][$eq]': _user_address}

                    response = await temp_client.get(url, params=params)

                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and len(data['data']) > 0:
                            return {
                                'valid': True,
                                'message': 'User found on Polymarket',
                                'data': data['data'][0]
                            }

                    # Try alternative: check if we can get any data about this address
                    # Using data API to look for trades
                    data_url = "{}/trades?maker={}".format(self._data_url, _user_address)
                    response2 = await temp_client.get(data_url)

                    if response2.status_code == 200:
                        trades_data = response2.json()
                        if trades_data and len(trades_data) > 0:
                            return {
                                'valid': True,
                                'message': 'User found on Polymarket',
                                'data': trades_data[0]
                            }

            except Exception as api_error:
                # If API is unreachable (VPN required, DNS error, etc.)
                # Accept the address format validation only
                self._logger.warning("Polymarket API unreachable: {}".format(str(api_error)))
                return {
                    'valid': True,
                    'message': 'Address format valid (API offline - VPN may be required for full validation)',
                    'offline_mode': True
                }

            return {
                'valid': False,
                'message': 'User address not found on Polymarket'
            }

        except Exception as e:
            self._logger.error("User validation failed: {}".format(str(e)))
            return {
                'valid': False,
                'message': 'Validation error: {}'.format(str(e))
            }

    async def get_user_recent_activity(self, _user_address, _limit=10):
        """
        Get recent trading activity for a user address.
        Uses multiple Polymarket APIs to fetch recent trades.

        Args:
            _user_address: Ethereum address of user
            _limit: Number of recent activities to return

        Returns:
            List of recent activities
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as temp_client:
                # Try data API first (most comprehensive trade data)
                url = "{}/trades".format(self._data_url)
                params = {
                    'maker': _user_address,
                    '_limit': _limit,
                    '_sort': 'timestamp:desc'
                }

                response = await temp_client.get(url, params=params)

                if response.status_code == 200:
                    trades = response.json()
                    if trades is not None and len(trades) > 0:
                        return trades

                # Fallback: Try CLOB API for order history
                clob_url = "{}/data/trades".format(self._clob_url)
                clob_params = {
                    'maker': _user_address,
                    'limit': _limit
                }

                clob_response = await temp_client.get(clob_url, params=clob_params)

                if clob_response.status_code == 200:
                    clob_trades = clob_response.json()
                    if clob_trades is not None and len(clob_trades) > 0:
                        return clob_trades

                # Return empty list if no data found
                return []

        except Exception as e:
            self._logger.error("Failed to get user activity: {}".format(str(e)))
            return []

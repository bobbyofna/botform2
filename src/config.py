"""
Configuration module for BotForm2.

Loads environment variables and provides configuration constants.
Follows bobbyofna coding style conventions.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration container for application settings."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Database configuration
        self._database_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/botform2')

        # Polymarket API configuration
        self._polymarket_api_key = os.getenv('POLYMARKET_API_KEY', '')
        self._polymarket_api_secret = os.getenv('POLYMARKET_API_SECRET', '')
        self._polymarket_base_url = os.getenv('POLYMARKET_BASE_URL', 'https://api.polymarket.com')

        # Security configuration
        self._require_vpn = os.getenv('REQUIRE_VPN', 'false').lower() == 'true'
        self._allowed_vpn_ips = os.getenv('ALLOWED_VPN_IPS', '').split(',') if os.getenv('ALLOWED_VPN_IPS', '') != '' else []

        # Application configuration
        self._env = os.getenv('ENV', 'development')
        self._log_level = os.getenv('LOG_LEVEL', 'INFO')
        self._host = os.getenv('HOST', '127.0.0.1')
        self._port = int(os.getenv('PORT', '8000'))

        # Bot configuration
        self._poll_interval = int(os.getenv('POLL_INTERVAL', '5'))  # seconds
        self._rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', '0.2'))  # seconds

    @property
    def database_url(self):
        """Get database connection URL."""
        return self._database_url

    @property
    def polymarket_api_key(self):
        """Get Polymarket API key."""
        return self._polymarket_api_key

    @property
    def polymarket_api_secret(self):
        """Get Polymarket API secret."""
        return self._polymarket_api_secret

    @property
    def polymarket_base_url(self):
        """Get Polymarket API base URL."""
        return self._polymarket_base_url

    @property
    def require_vpn(self):
        """Check if VPN is required."""
        return True if self._require_vpn == True else False

    @property
    def allowed_vpn_ips(self):
        """Get list of allowed VPN IP addresses/ranges."""
        return self._allowed_vpn_ips

    @property
    def env(self):
        """Get environment name."""
        return self._env

    @property
    def log_level(self):
        """Get logging level."""
        return self._log_level

    @property
    def host(self):
        """Get application host."""
        return self._host

    @property
    def port(self):
        """Get application port."""
        return self._port

    @property
    def poll_interval(self):
        """Get bot polling interval in seconds."""
        return self._poll_interval

    @property
    def rate_limit_delay(self):
        """Get API rate limit delay in seconds."""
        return self._rate_limit_delay

    @property
    def is_development(self):
        """Check if running in development mode."""
        return True if self._env == 'development' else False

    @property
    def is_production(self):
        """Check if running in production mode."""
        return True if self._env == 'production' else False


# Global configuration instance
config = Config()

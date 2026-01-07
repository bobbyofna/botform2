"""
VPN validation utility for BotForm2.

Checks if the application is running through ProtonVPN on Windows.
Follows bobbyofna coding style conventions.
"""

import logging
import subprocess
import httpx
import ipaddress
from typing import List, Optional


class VPNChecker:
    """VPN validation utility with ProtonVPN integration."""

    def __init__(self, _allowed_ips=None, _required=True):
        """
        Initialize VPN checker.

        Args:
            _allowed_ips: List of allowed IP addresses/ranges (CIDR notation)
            _required: Whether VPN is required
        """
        self._allowed_ips = [] if _allowed_ips is None else _allowed_ips
        self._required = _required
        self._logger = logging.getLogger(__name__)
        self._public_ip = None
        self._protonvpn_connected = False

    @property
    def public_ip(self):
        """Get the detected public IP address."""
        return self._public_ip

    @property
    def is_required(self):
        """Check if VPN is required."""
        return True if self._required == True else False

    @property
    def protonvpn_connected(self):
        """Check if ProtonVPN is connected."""
        return True if self._protonvpn_connected == True else False

    def _check_protonvpn_status(self):
        """
        Check if ProtonVPN is connected on Windows.

        Returns:
            True if ProtonVPN is connected, False otherwise
        """
        try:
            # Check if ProtonVPN process is running
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq ProtonVPN.exe'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                output = result.stdout.lower()
                if 'protonvpn.exe' in output:
                    self._logger.info("ProtonVPN process detected")

                    # Try to get VPN adapter status
                    adapter_result = subprocess.run(
                        ['netsh', 'interface', 'show', 'interface'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if adapter_result.returncode == 0:
                        adapter_output = adapter_result.stdout.lower()
                        # ProtonVPN typically uses TAP or WireGuard adapter
                        vpn_indicators = ['proton', 'tap', 'wireguard', 'wintun']
                        i = 0
                        for indicator in vpn_indicators:
                            if indicator in adapter_output and 'connected' in adapter_output:
                                self._logger.info("ProtonVPN adapter active: {}".format(indicator))
                                self._protonvpn_connected = True
                                return True
                            i = i + 1

                    # Process running but adapter not confirmed - assume connected
                    self._protonvpn_connected = True
                    return True

            self._logger.info("ProtonVPN not detected")
            self._protonvpn_connected = False
            return False

        except subprocess.TimeoutExpired:
            self._logger.error("Timeout checking ProtonVPN status")
            return False
        except Exception as e:
            self._logger.error("Error checking ProtonVPN status: {}".format(str(e)))
            return False

    async def get_public_ip(self):
        """
        Fetch public IP address from external service.

        Returns:
            Public IP address as string
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get('https://api.ipify.org?format=json')
                if response.status_code == 200:
                    data = response.json()
                    self._public_ip = data.get('ip', None)
                    self._logger.info("Detected public IP: {}".format(self._public_ip))
                    return self._public_ip
                else:
                    self._logger.error("Failed to get public IP: HTTP {}".format(response.status_code))
                    return None

        except Exception as e:
            self._logger.error("Error fetching public IP: {}".format(str(e)))
            return None

    def _ip_in_range(self, _ip, _ip_range):
        """
        Check if IP is in given range.

        Args:
            _ip: IP address to check
            _ip_range: IP range in CIDR notation (e.g., '192.168.1.0/24')

        Returns:
            True if IP is in range, False otherwise
        """
        try:
            ip_obj = ipaddress.ip_address(_ip)
            network_obj = ipaddress.ip_network(_ip_range, strict=False)
            result = True if ip_obj in network_obj else False
            return result

        except Exception as e:
            self._logger.error("Error checking IP range: {}".format(str(e)))
            return False

    async def check_vpn_status(self):
        """
        Check if ProtonVPN is connected and IP is within allowed ranges.

        Returns:
            True if VPN is valid or not required, False otherwise
        """
        # If VPN not required, always return True
        if self.is_required == False:
            self._logger.info("VPN check disabled")
            return True

        # Check ProtonVPN status
        proton_connected = self._check_protonvpn_status()

        if proton_connected == False:
            self._logger.error("ProtonVPN is not connected")
            return False

        self._logger.info("ProtonVPN connection verified")

        # If no allowed IPs configured, just check ProtonVPN connection
        if len(self._allowed_ips) == 0:
            self._logger.info("No IP ranges configured, accepting any ProtonVPN connection")
            return True

        # Get public IP
        public_ip = await self.get_public_ip()

        if public_ip is None:
            self._logger.error("Could not determine public IP")
            return False

        # Check if IP is in any allowed range
        i = 0
        for ip_range in self._allowed_ips:
            ip_range = ip_range.strip()
            if ip_range == '':
                i = i + 1
                continue

            if self._ip_in_range(public_ip, ip_range) == True:
                self._logger.info("VPN check passed: {} in {}".format(public_ip, ip_range))
                return True

            i = i + 1

        # IP not in any allowed range
        self._logger.error("VPN check failed: {} not in allowed ranges".format(public_ip))
        return False

    async def validate_or_exit(self):
        """
        Validate VPN status and exit application if check fails.

        Raises:
            SystemExit if VPN check fails
        """
        result = await self.check_vpn_status()

        if result == False:
            self._logger.critical("VPN validation failed, exiting application")
            raise SystemExit(1)
        else:
            self._logger.info("VPN validation passed")
            return True

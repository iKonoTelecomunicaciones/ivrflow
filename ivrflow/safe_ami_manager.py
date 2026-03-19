from __future__ import annotations

import asyncio

from aioagi.ami.manager import AMIManager
from aioagi.log import agi_ami_logger


class SafeAMIManager(AMIManager):
    """
    Wrapper for AMIManager to avoid multiple reconnects simultaneously.

    In `aioagi.ami.manager.AMIManager`, `connection_lost()` calls
    `asyncio.ensure_future(self.connect())`. If for any reason multiple `connection_lost()` are triggered
    in a row, multiple `connect()` coroutines can accumulate and compete for the event loop,
    causing a resource exhaustion."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._connect_lock = asyncio.Lock()

    async def connect(self):
        """Connect to the Asterisk server and serialize the reconnects.
        This is a workaround to avoid multiple reconnects at the same time.
        If multiple reconnects are triggered, they can accumulate and compete for the event loop,
        causing a resource exhaustion."""
        async with self._connect_lock:
            return await super().connect()

    def connection_lost(self, exc):
        """Handle the connection lost event"""
        self.connected = self.authenticated = False

        agi_ami_logger.info(f"{self.title}: Asterisk connection lost!")
        exc and agi_ami_logger.warning(exc)

        if self.authenticator:
            self.authenticator.cancel()
            self.authenticator = None

        if self.pinger:
            self.pinger.cancel()
            self.pinger = None

        if not self.closed:
            self.store_actions()
            agi_ami_logger.info(f"{self.title}: Try to connect again")
            if not self._connect_lock.locked():
                asyncio.ensure_future(self.connect())

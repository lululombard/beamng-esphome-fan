"""
ESPHome connection and fan control.
"""

import asyncio
import threading
import aioesphomeapi

from config import Config, LiveData


class ESPHomeClient:
    """
    Manages connection to ESPHome device and fan control.
    """
    def __init__(self):
        self.api = None
        self.fan_entity = None
        self.lock = threading.Lock()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3

    async def connect(self):
        """
        Connect to ESPHome device and retrieve the fan entity.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create API client with IP from configuration, port 6053, no password
            api = aioesphomeapi.APIClient(Config.ESP_IP, 6053, None)
            # Connect to the ESPHome device
            await api.connect(login=True)

            # List all entities available on the device
            entities = await api.list_entities_services()

            # Search for the fan entity specified in configuration
            entity = None
            for ent in entities[0]:
                if ent.object_id == Config.FAN_ENTITY:
                    entity = ent
                    break

            with self.lock:
                self.api = api
                self.fan_entity = entity

            if not entity:
                print(f"Warning: Fan entity '{Config.FAN_ENTITY}' not found")
                LiveData.set_connected(False)
                return False

            print(f"Connected to ESPHome fan: {entity.name}")
            LiveData.set_connected(True)
            return True

        except Exception as e:
            print(f"Error connecting to ESPHome: {e}")
            with self.lock:
                self.api = None
                self.fan_entity = None
            LiveData.set_connected(False)
            return False

    def reconnect(self):
        """
        Reconnect to ESPHome with current settings (synchronous wrapper).

        Returns:
            bool: True if connection successful, False otherwise
        """
        print(f"Connecting to ESPHome at {Config.ESP_IP}...")
        success = asyncio.run(self.connect())
        if success:
            self.reconnect_attempts = 0  # Reset counter on successful connection
        return success

    async def control_fan(self, fan_speed):
        """
        Send fan control command to ESPHome device asynchronously.

        Args:
            fan_speed: Target fan speed percentage (0-100)
        """
        with self.lock:
            if self.api is None or self.fan_entity is None:
                return  # Silently skip if not connected

            try:
                # Send fan command: turn on if speed > 0, and set the speed level
                await self.api.fan_command(
                    self.fan_entity.key,
                    fan_speed > 0,
                    speed_level=fan_speed
                )
                self.reconnect_attempts = 0  # Reset on successful command
            except Exception as e:
                # Connection lost - mark as disconnected and trigger reconnection
                print(f"[ERROR] ESPHome connection lost: {e}")
                self.api = None
                self.fan_entity = None
                LiveData.set_connected(False)

                # Attempt to reconnect if we haven't exceeded max attempts
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    print(f"[INFO] Attempting reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")

    def update_fan_speed(self, fan_speed):
        """
        Wrapper function to run async ESPHome command from synchronous context.
        Automatically attempts reconnection if the connection is lost.

        Args:
            fan_speed: Target fan speed percentage (0-100)
        """
        asyncio.run(self.control_fan(fan_speed))

        # If we detected a connection failure, attempt to reconnect
        if not self.is_connected() and self.reconnect_attempts > 0 and self.reconnect_attempts <= self.max_reconnect_attempts:
            if self.reconnect():
                print("[OK] Reconnected successfully")
                # Retry the command after successful reconnection
                asyncio.run(self.control_fan(fan_speed))
            else:
                print(f"[WARN] Reconnection failed ({self.reconnect_attempts}/{self.max_reconnect_attempts})")

    def is_connected(self):
        """Check if connected to ESPHome."""
        with self.lock:
            return self.api is not None and self.fan_entity is not None

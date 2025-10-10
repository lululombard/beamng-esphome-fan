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
        return asyncio.run(self.connect())

    async def control_fan(self, fan_speed):
        """
        Send fan control command to ESPHome device asynchronously.

        Args:
            fan_speed: Target fan speed percentage (0-100)
        """
        with self.lock:
            if self.api is None or self.fan_entity is None:
                print("ESPHome not connected")
                return

            try:
                # Send fan command: turn on if speed > 0, and set the speed level
                await self.api.fan_command(
                    self.fan_entity.key,
                    fan_speed > 0,
                    speed_level=fan_speed
                )
            except Exception as e:
                print(f"Error controlling fan: {e}")

    def update_fan_speed(self, fan_speed):
        """
        Wrapper function to run async ESPHome command from synchronous context.

        Args:
            fan_speed: Target fan speed percentage (0-100)
        """
        asyncio.run(self.control_fan(fan_speed))

    def is_connected(self):
        """Check if connected to ESPHome."""
        with self.lock:
            return self.api is not None and self.fan_entity is not None

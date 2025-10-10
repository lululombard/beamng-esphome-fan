#!/usr/bin/env python3
"""
BeamNG to ESPHome Fan Controller

This script receives vehicle speed data from BeamNG.drive via UDP (using the OutGauge protocol)
and controls a physical fan connected to an ESPHome device based on the in-game speed.
The fan speed is proportional to the vehicle speed in the game, creating a realistic driving experience.

Includes a Flask web interface to modify settings in real-time.
"""

import asyncio

from config import Config
from esphome_client import ESPHomeClient
from beamng_monitor import BeamNGMonitor
from web_server import WebServer


def main():
    """
    Main entry point of the application.

    Loads settings, initializes ESPHome connection, starts Flask web server in a thread,
    and begins monitoring BeamNG vehicle speed.
    """
    print("=" * 60)
    print("  BeamNG ESPHome Fan Controller")
    print("=" * 60)

    # Load saved settings
    print("\n[1/4] Loading configuration...")
    Config.load_from_file()

    # Initialize ESPHome client
    print("[2/4] Initializing ESPHome client...")
    esphome_client = ESPHomeClient()

    # Connect to ESPHome if configured
    if Config.ESP_IP and Config.FAN_ENTITY:
        print(f"      Connecting to {Config.ESP_IP}...")
        if esphome_client.reconnect():
            print("      [OK] ESPHome connected successfully")
        else:
            print("      [WARN] Could not connect to ESPHome")
            print("      Configure settings in web interface")
    else:
        print("      [WARN] ESP_IP or FAN_ENTITY not configured")
        print("      Configure in web interface at http://localhost:5000")

    # Start web server in background thread
    print("[3/4] Starting web interface...")
    web_server = WebServer(esphome_client)
    web_server.run_in_thread()
    print("      [OK] Web interface available at http://localhost:5000")

    # Start BeamNG monitor (blocking)
    print("[4/4] Starting BeamNG monitor...")
    print("\n" + "=" * 60)
    print("  System ready! Configure at http://localhost:5000")
    print("=" * 60 + "\n")

    monitor = BeamNGMonitor(esphome_client)

    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        # Turn off fan before exit
        if esphome_client.is_connected():
            print("Stopping fan...")
            asyncio.run(esphome_client.control_fan(0))
        print("Goodbye!")


if __name__ == '__main__':
    main()

"""
Configuration management for BeamNG ESPHome Fan Controller.
"""

import json
import time
import threading
from pathlib import Path

# Settings file path
SETTINGS_FILE = Path(__file__).parent / "settings.json"


class Config:
    """
    Application configuration that can be modified at runtime via web interface.
    Settings are persisted to settings.json file.
    """
    # Fan Speed Mapping
    MIN_SPEED_KMH = 0      # Vehicle speed (km/h) that maps to 0% fan speed
    MAX_SPEED_KMH = 300    # Vehicle speed (km/h) that maps to 100% fan speed

    # Fan Speed Limits
    MIN_FAN_SPEED = 0      # Minimum fan speed (0 = off, 1+ = always on at minimum level)
    MAX_FAN_SPEED = 100    # Maximum fan speed percentage

    # Command Rate Limiting
    COOLDOWN_MS = 300      # Cooldown between fan commands in milliseconds

    # Rate Compensation (Derivative Control)
    RATE_COMPENSATION = 0  # 0-100: How much to react to speed changes (0=off, higher=more aggressive)
    RATE_SMOOTHING = 3     # Number of speed samples to average (higher=smoother, less reactive)

    # System Control
    ENABLED = True         # Master switch to enable/disable the system

    # ESPHome Configuration
    ESP_IP = "192.168.99.100"
    FAN_ENTITY = "fan"

    @classmethod
    def to_dict(cls):
        """Convert configuration to dictionary."""
        return {
            'MIN_SPEED_KMH': cls.MIN_SPEED_KMH,
            'MAX_SPEED_KMH': cls.MAX_SPEED_KMH,
            'MIN_FAN_SPEED': cls.MIN_FAN_SPEED,
            'MAX_FAN_SPEED': cls.MAX_FAN_SPEED,
            'COOLDOWN_MS': cls.COOLDOWN_MS,
            'RATE_COMPENSATION': cls.RATE_COMPENSATION,
            'RATE_SMOOTHING': cls.RATE_SMOOTHING,
            'ENABLED': cls.ENABLED,
            'ESP_IP': cls.ESP_IP,
            'FAN_ENTITY': cls.FAN_ENTITY,
        }

    @classmethod
    def update_from_dict(cls, data):
        """Update configuration from dictionary."""
        cls.MIN_SPEED_KMH = data.get('MIN_SPEED_KMH', cls.MIN_SPEED_KMH)
        cls.MAX_SPEED_KMH = data.get('MAX_SPEED_KMH', cls.MAX_SPEED_KMH)
        cls.MIN_FAN_SPEED = data.get('MIN_FAN_SPEED', cls.MIN_FAN_SPEED)
        cls.MAX_FAN_SPEED = data.get('MAX_FAN_SPEED', cls.MAX_FAN_SPEED)
        cls.COOLDOWN_MS = data.get('COOLDOWN_MS', cls.COOLDOWN_MS)
        cls.RATE_COMPENSATION = data.get('RATE_COMPENSATION', cls.RATE_COMPENSATION)
        cls.RATE_SMOOTHING = data.get('RATE_SMOOTHING', cls.RATE_SMOOTHING)
        cls.ENABLED = data.get('ENABLED', cls.ENABLED)
        cls.ESP_IP = data.get('ESP_IP', cls.ESP_IP)
        cls.FAN_ENTITY = data.get('FAN_ENTITY', cls.FAN_ENTITY)

    @classmethod
    def save_to_file(cls):
        """Save configuration to JSON file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(cls.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    @classmethod
    def load_from_file(cls):
        """Load configuration from JSON file."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    cls.update_from_dict(data)
                print(f"Loaded settings from {SETTINGS_FILE}")
                return True
        except Exception as e:
            print(f"Error loading settings: {e}")
        return False


class LiveData:
    """
    Store current live data for streaming to web interface.
    """
    current_speed_kmh = 0.0
    current_fan_speed = 0
    rate_compensation_value = 0  # Current compensation being applied
    connected = False
    last_update = time.time()
    lock = threading.Lock()

    @classmethod
    def update(cls, speed_kmh, fan_speed, compensation=0):
        """Update live data."""
        with cls.lock:
            cls.current_speed_kmh = speed_kmh
            cls.current_fan_speed = fan_speed
            cls.rate_compensation_value = compensation
            cls.last_update = time.time()

    @classmethod
    def set_connected(cls, connected):
        """Update connection status."""
        with cls.lock:
            cls.connected = connected

    @classmethod
    def to_dict(cls):
        """Get live data as dictionary."""
        with cls.lock:
            return {
                'speed_kmh': round(cls.current_speed_kmh, 1),
                'fan_speed': cls.current_fan_speed,
                'rate_compensation': round(cls.rate_compensation_value, 1),
                'enabled': Config.ENABLED,
                'connected': cls.connected,
                'timestamp': cls.last_update
            }

"""
BeamNG OutGauge UDP monitor for vehicle speed tracking.
"""

import socket
import struct
import time

from config import Config, LiveData


class BeamNGMonitor:
    """
    Monitor BeamNG OutGauge UDP stream and track vehicle speed.
    """
    def __init__(self, esphome_client):
        """
        Initialize the monitor.

        Args:
            esphome_client: ESPHomeClient instance for fan control
        """
        self.esphome_client = esphome_client
        self.previous_fan_speed = 0
        self.previous_speed = 0.0
        self.previous_time = time.time()
        self.command_cooldown = time.time_ns()
        self.speed_history = []  # Rolling buffer for speed smoothing

    def start(self):
        """
        Start monitoring BeamNG vehicle speed (blocking).

        This function creates a UDP socket to receive telemetry data from BeamNG.drive.
        When the speed changes, it calculates an appropriate fan speed and triggers
        the ESPHome client to update the physical fan.
        """
        # Create UDP socket for receiving BeamNG telemetry data
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)  # Add timeout to check enabled state periodically

        # Bind to BeamNG OutGauge port (default: 4444)
        # Listen on all interfaces (0.0.0.0)
        sock.bind(("0.0.0.0", 4444))

        print("Monitoring BeamNG vehicle speed...")

        while True:
            try:
                # Receive 96 bytes of OutGauge data from BeamNG
                data = sock.recv(96)

                if not data:
                    break  # Lost connection to BeamNG

                # Unpack the OutGauge binary data structure
                # Format: I (uint), 4s (4 chars), H (ushort), 2c (2 chars), 7f (7 floats),
                #         2I (2 uints), 3f (3 floats), 16s (16 chars), 16s (16 chars), i (int)
                outgauge_data = struct.unpack("I4sH2c7f2I3f16s16si", data)

                # Extract speed from the data (index 5) and convert from m/s to km/h
                speed = round(outgauge_data[5] * 3.6, 2)  # km/h

                # Calculate fan speed based on configuration
                base_fan_speed = self._calculate_fan_speed(speed)

                # Apply rate compensation (derivative control) if enabled
                compensation = 0
                if Config.RATE_COMPENSATION > 0:
                    fan_speed, compensation = self._apply_rate_compensation(speed, base_fan_speed)
                else:
                    fan_speed = base_fan_speed

                # If system is disabled, force fan speed to 0
                if not Config.ENABLED:
                    fan_speed = 0
                    compensation = 0

                # Update live data for web interface
                LiveData.update(speed, fan_speed, compensation)

                # Only send command if fan speed changed and cooldown period has elapsed
                if fan_speed != self.previous_fan_speed and self.command_cooldown < time.time_ns():
                    self.previous_fan_speed = fan_speed
                    # Convert cooldown from milliseconds to nanoseconds
                    self.command_cooldown = time.time_ns() + (Config.COOLDOWN_MS * 1_000_000)
                    # Trigger the ESPHome client to update the physical fan
                    self.esphome_client.update_fan_speed(fan_speed)

                    # Print debug info with rate compensation details
                    if Config.RATE_COMPENSATION > 0 and compensation != 0:
                        comp_sign = '+' if compensation > 0 else ''
                        comp_color = '\033[92m' if compensation > 0 else '\033[91m'  # Green or Red
                        reset_color = '\033[0m'
                        print("Vehicle: {:.1f} km/h | Fan: {}% | Rate Comp: {}{}{:.1f}{}{}".format(
                            speed, fan_speed, comp_color, comp_sign, compensation, reset_color,
                            " (DISABLED)" if not Config.ENABLED else ""))
                    else:
                        print("Vehicle: {:.1f} km/h | Fan: {}%{}".format(
                            speed, fan_speed, " (DISABLED)" if not Config.ENABLED else ""))

            except socket.timeout:
                # Timeout allows us to check if system is still running
                # Update live data to show 0 speed when no data received
                LiveData.update(0, 0 if not Config.ENABLED else self.previous_fan_speed, 0)
                continue
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(1)

        # Clean up socket when loop exits
        sock.close()

    def _calculate_fan_speed(self, speed):
        """
        Calculate fan speed as a percentage based on vehicle speed.

        Args:
            speed: Vehicle speed in km/h

        Returns:
            int: Fan speed percentage (0-100)
        """
        # Map vehicle speed linearly from MIN_SPEED_KMH-MAX_SPEED_KMH to min-max fan speed
        if speed <= Config.MIN_SPEED_KMH:
            return Config.MIN_FAN_SPEED
        elif speed >= Config.MAX_SPEED_KMH:
            return Config.MAX_FAN_SPEED
        else:
            # Linear interpolation between min and max speed
            speed_range = Config.MAX_SPEED_KMH - Config.MIN_SPEED_KMH
            fan_range = Config.MAX_FAN_SPEED - Config.MIN_FAN_SPEED
            return Config.MIN_FAN_SPEED + round(((speed - Config.MIN_SPEED_KMH) / speed_range) * fan_range)

    def _apply_rate_compensation(self, current_speed, base_fan_speed):
        """
        Apply rate compensation (derivative control) to fan speed with smoothing.

        This makes the fan respond more aggressively to acceleration/deceleration,
        anticipating speed changes to reduce lag. Uses rolling average for smoothing.

        Args:
            current_speed: Current vehicle speed in km/h
            base_fan_speed: Base fan speed calculated from current speed

        Returns:
            tuple: (adjusted fan speed, compensation value)
                - int: Adjusted fan speed with rate compensation applied (clamped)
                - float: Compensation value applied (positive=accelerating, negative=braking)
        """
        current_time = time.time()
        time_delta = current_time - self.previous_time

        # Avoid division by zero and only calculate if enough time has passed
        if time_delta < 0.01:  # At least 10ms between calculations
            return base_fan_speed, 0

        # Add current speed to history for smoothing
        self.speed_history.append(current_speed)
        if len(self.speed_history) > Config.RATE_SMOOTHING:
            self.speed_history.pop(0)

        # Use smoothed speed for derivative calculation
        if len(self.speed_history) >= 2:
            smoothed_speed = sum(self.speed_history) / len(self.speed_history)
        else:
            smoothed_speed = current_speed

        # Calculate rate of speed change (km/h per second) using smoothed values
        speed_change_rate = (smoothed_speed - self.previous_speed) / time_delta

        # Update previous values for next iteration
        self.previous_speed = smoothed_speed
        self.previous_time = current_time

        # Calculate derivative component with reduced sensitivity
        # Positive rate = accelerating, negative = decelerating
        # Scale by rate compensation factor (0-100) and divide by 50 for lower sensitivity
        derivative_component = (speed_change_rate * Config.RATE_COMPENSATION) / 50

        # Apply derivative to base fan speed
        compensated_speed = base_fan_speed + derivative_component

        # Smart clamping: Don't let compensation bring fan too far from base speed
        # Maximum compensation is ±30% of current base speed (prevents absurd values)
        max_deviation = max(30, base_fan_speed * 0.5)
        compensated_speed = max(base_fan_speed - max_deviation,
                              min(base_fan_speed + max_deviation, compensated_speed))

        # Final clamp to valid fan speed range
        compensated_speed = max(Config.MIN_FAN_SPEED, min(Config.MAX_FAN_SPEED, round(compensated_speed)))

        # Return both the compensated speed and the actual compensation applied
        actual_compensation = compensated_speed - base_fan_speed

        return compensated_speed, actual_compensation

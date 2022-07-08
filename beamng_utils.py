import socket
import struct
import time


def subscribe_speed(callback, *args, **kwargs):
    # Create UDP socket.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to BeamNG OutGauge.
    sock.bind(("0.0.0.0", 4444))

    previous_fan_speed = 0

    command_cooldown = time.time_ns()

    while True:
        # Receive data.
        data = sock.recv(96)

        if not data:
            break  # Lost connection

        # Unpack the data.
        outsim_pack = struct.unpack("I4sH2c7f2I3f16s16si", data)

        speed = round(outsim_pack[5] * 3.6, 2)  # km/h

        fan_speed = round(1 + speed / 3)

        if fan_speed > 100:
            fan_speed = 100

        if fan_speed != previous_fan_speed and command_cooldown < time.time_ns():
            previous_fan_speed = fan_speed
            command_cooldown = time.time_ns() + 300000000  # 0.3sec
            callback(fan_speed, *args, **kwargs)
            print("Fan speed: {}".format(fan_speed))

    # Release the socket.
    sock.close()

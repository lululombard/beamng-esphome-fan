import os

import requests
from dotenv import load_dotenv

from beamng_utils import subscribe_speed

load_dotenv()


def set_fan_speed(fan_speed):
    requests.post(
        "http://{}/fan/{}/turn_on?speed_level={}".format(
            os.environ.get("ESP_IP"), os.environ.get("FAN_ENTITY"), fan_speed
        )
    )


subscribe_speed(set_fan_speed)

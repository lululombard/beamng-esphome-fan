import os

from homeassistant_api import Client
from dotenv import load_dotenv

from beamng_utils import subscribe_speed

load_dotenv()


def set_fan_speed(fan_speed, client):
    client.get_domain("fan").turn_on(
        entity_id="fan.{}".format(os.environ.get("FAN_ENTITY")), percentage=fan_speed
    )


with Client(os.environ.get("HA_API"), os.environ.get("HA_TOKEN")) as client:
    subscribe_speed(set_fan_speed, client)

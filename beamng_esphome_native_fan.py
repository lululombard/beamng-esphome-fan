import os
import asyncio

import aioesphomeapi
from dotenv import load_dotenv

from beamng_utils import subscribe_speed

load_dotenv()


async def send_esphome_command(fan_speed, api: aioesphomeapi.APIClient, fan):
    await api.fan_command(fan.key, True, speed_level=fan_speed)


def set_fan_speed(fan_speed, api, fan):
    asyncio.run(send_esphome_command(fan_speed, api, fan))


async def get_fan_api():
    api = aioesphomeapi.APIClient(os.environ.get("ESP_IP"), 6053, None)
    await api.connect(login=True)
    # List all entities of the device
    entities = await api.list_entities_services()
    fan = None
    for entity in entities[0]:
        if entity.object_id == os.environ.get("FAN_ENTITY"):
            fan = entity
            break

    return api, fan


api, fan = asyncio.run(get_fan_api())

if not fan:
    raise ValueError("fan entity not found, check FAN_ENTITY config")

subscribe_speed(set_fan_speed, api, fan)

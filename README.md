# ESPHome/Home Assistant BeamNG integration

:warning: This is not a finished product and probably will never be, it's an experiment to connect the BemaNG OutGauge protocol to an ESPHome fan.

The solution that seems to be working the best is the beamng_esphome_native_fan.py which uses ESPHome's native API (the one HA uses to communicate with your ESP).

## How do I make this work?

This has only been tested on Linux (Ubuntu 20.04)

First, run `python3.10 -m venv env` to create a venv, then `source env/bin/activate` to activate it, `pip install -r requirements.txt` to install libraries, `cp .env.example .env` to copy the default config, then edit that `.env` file with your info (no need to setup HA if you use the Native or REST ESPHome API directly), then you only need to run the flavor you want of my tool, e.g. `python beamng_esphome_native_fan.py`. In BeamNG, you'll have to go in Options > Other > Utilities > OutGauge support (make sure it's enabled) and set the IP to whatever your server running the python tool is. Reload your car and it should work!

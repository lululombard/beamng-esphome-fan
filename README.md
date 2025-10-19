# BeamNG ESPHome Fan Controller

Control a physical fan with your vehicle speed in BeamNG.drive! This tool receives telemetry data from BeamNG via the OutGauge protocol and controls an ESPHome fan in real-time, creating an immersive driving experience with wind in your face.

## Features

- **Real-time fan control** based on vehicle speed
- **Web interface** for configuration and monitoring (http://localhost:5000)
- **Live data display** - see current speed, fan speed, and rate compensation in real-time
- **Persistent settings** - configuration saved to `settings.json`
- **Customizable speed mapping** - configure min/max speeds and fan levels
- **Rate compensation** - derivative control for aggressive response to acceleration/braking
- **Dynamic ESPHome connection** - configure IP and entity from the web UI
- **Global on/off switch** - disable the system without stopping the script
- **Automatic reconnection** - automatically reconnects when ESPHome connection is lost (up to 3 attempts)

## Requirements

- Python 3.8+
- ESPHome device with a fan entity
- BeamNG.drive with OutGauge enabled
- Linux, Windows, or macOS

## Quick Start

### 1. Setup Virtual Environment

```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python beamng_esphome_fan.py
```

The web interface will be available at **http://localhost:5000**

### 3. Configure BeamNG.drive

1. In BeamNG.drive, go to: **Options > Other > Utilities > OutGauge Support**
2. Enable OutGauge
3. Set IP to your computer's IP address
4. Set Port to `4444` (default)
5. Reload your vehicle

> **Note**: Due to OutGauge protocol limitations, the system uses **wheel speed** rather than actual vehicle speed. This means:
> - Locking wheels during hard braking (without ABS) will stop the fan even if you're still moving
> - Doing a burnout with spinning wheels will make the fan spin fast even while stationary
> - This is a limitation of the OutGauge protocol, not this software

## Usage

### Web Interface

Open http://localhost:5000 in your browser to:

- **View live data**: Current vehicle speed, fan speed, rate compensation, and ESPHome connection status
- **System controls**:
  - Enable/Disable the system with a toggle switch
- **Algorithm configuration**:
  - Speed mapping (0-300 km/h by default)
  - Fan speed limits (0-100%)
  - Rate compensation for responsive acceleration/braking
  - Rate smoothing for stable derivative calculations
- **ESPHome connection**:
  - ESPHome IP address and fan entity
  - Command cooldown (300ms by default)
  - Save & reconnect functionality

### Configuration Options

#### Algorithm Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| **Min Vehicle Speed (km/h)** | Vehicle speed that maps to 0% fan | 0 |
| **Max Vehicle Speed (km/h)** | Vehicle speed that maps to 100% fan | 300 |
| **Min Fan Speed (%)** | Minimum fan speed (0=off, 1+=always on) | 0 |
| **Max Fan Speed (%)** | Maximum fan speed cap | 100 |
| **Rate Compensation** | How aggressively to respond to speed changes (0=off, 20-40=balanced, 60+=aggressive) | 0 |
| **Rate Smoothing** | Number of speed samples to average for derivative (1=instant, 3=balanced, 10=smooth) | 3 |

#### ESPHome Connection

| Setting | Description | Default |
|---------|-------------|---------|
| **ESP IP** | IP address of your ESPHome device | - |
| **Fan Entity** | ESPHome fan entity object_id | - |
| **Cooldown (ms)** | Delay between fan commands (prevents device overload) | 300 |

**Examples:**
- Set **Min Fan Speed = 1** to keep the fan always on at minimum level
- Set **Max Vehicle Speed = 200** to reach 100% fan speed at 200 km/h instead of 300
- Set **Cooldown = 500** to reduce ESPHome command frequency
- Set **Rate Compensation = 30-40** for more responsive fan during acceleration/braking
- Set **Rate Smoothing = 5-7** for smoother but less reactive compensation

## Project Structure

```
beamng-esphome-fan/
├── beamng_esphome_fan.py    # Main entry point
├── config.py                 # Configuration management & live data
├── esphome_client.py         # ESPHome connection & fan control
├── beamng_monitor.py         # BeamNG UDP telemetry monitoring & rate compensation
├── web_server.py             # Flask web interface & API
├── templates/
│   └── index.html            # Web UI template (BeamNG themed)
├── settings.json             # Saved configuration (auto-generated)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Troubleshooting

### Fan not responding?
1. Check ESPHome IP and fan entity in the web interface
2. Click "Save & Reconnect" button in the ESPHome Connection section
3. Verify your ESPHome device is online and accessible
4. Check that the fan entity ID matches exactly (it's the object_id, not the friendly name)

### No speed data?
1. Verify BeamNG OutGauge is enabled and configured correctly
2. Check that the IP in BeamNG matches your computer's IP
3. Make sure port 4444 is not blocked by firewall
4. Look for console output showing "Vehicle: X.X km/h | Fan: X%"

### Web interface not loading?
1. Check that port 5000 is not in use by another application
2. Try accessing via your computer's IP instead of localhost
3. Check console output for any Flask errors

### ESPHome connection keeps dropping?
The system automatically attempts to reconnect up to 3 times when the connection is lost:
- Look for `[ERROR] ESPHome connection lost` messages in console
- Check if your ESPHome device is stable (power, network)
- If reconnection fails repeatedly, manually click "Save & Reconnect" in the web UI
- After 3 failed attempts, manual reconnection is required

### Rate compensation behaving erratically?
1. Increase **Rate Smoothing** to 5-10 for more stable calculations
2. Decrease **Rate Compensation** to 20-30 for less aggressive response
3. Set **Rate Compensation** to 0 to disable derivative control entirely

### Fan behavior seems weird during braking/burnouts?
This is normal! OutGauge reports **wheel speed**, not vehicle speed:
- Hard braking with locked wheels (no ABS) → fan stops even though you're moving
- Burnouts with spinning wheels → fan spins fast even though you're stationary
- This is how the OutGauge protocol works and cannot be changed

## Advanced

### Running as a Service (Linux systemd)

Create `/etc/systemd/system/beamng-fan.service`:

```ini
[Unit]
Description=BeamNG ESPHome Fan Controller
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/beamng-esphome-fan
ExecStart=/path/to/beamng-esphome-fan/env/bin/python beamng_esphome_fan.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable beamng-fan
sudo systemctl start beamng-fan
```

### Rate Compensation (Derivative Control)

Rate compensation adds predictive behavior to the fan control by calculating the rate of speed change (acceleration/braking). This makes the fan:
- **Speed up faster** when you accelerate hard
- **Slow down faster** when you brake hard

The **Rate Compensation** slider controls the intensity (0-100), and **Rate Smoothing** controls how many speed samples are averaged to prevent jittery behavior. A good starting point is 30-40 for compensation and 3-5 for smoothing.

## License

This is an experimental project. Use at your own risk!

## Contributing

Feel free to open issues or submit pull requests for improvements.

---

**Enjoy your immersive racing experience!**

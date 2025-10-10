"""
Flask web server for configuration and monitoring interface.
"""

import json
import time
import asyncio
import threading
from flask import Flask, render_template, request, jsonify, Response

from config import Config, LiveData


class WebServer:
    """
    Flask web server for the BeamNG Fan Controller.
    """
    def __init__(self, esphome_client):
        """
        Initialize the web server.

        Args:
            esphome_client: ESPHomeClient instance
        """
        self.app = Flask(__name__)
        self.esphome_client = esphome_client
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes."""
        self.app.route('/')(self.index)
        self.app.route('/api/live')(self.live_data)
        self.app.route('/api/config', methods=['GET'])(self.get_config)
        self.app.route('/api/config', methods=['POST'])(self.update_config)
        self.app.route('/api/toggle', methods=['POST'])(self.toggle_system)
        self.app.route('/api/force-stop', methods=['POST'])(self.force_stop)
        self.app.route('/api/reconnect', methods=['POST'])(self.reconnect)

    def index(self):
        """Render the configuration page."""
        return render_template('index.html', config=Config.to_dict())

    def live_data(self):
        """Server-Sent Events endpoint for live data streaming."""
        def generate():
            while True:
                data = LiveData.to_dict()
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(0.5)  # Update twice per second

        return Response(generate(), mimetype='text/event-stream')

    def get_config(self):
        """Get current configuration as JSON."""
        return jsonify(Config.to_dict())

    def update_config(self):
        """Update configuration from JSON and save to file."""
        try:
            data = request.get_json()
            Config.update_from_dict(data)
            Config.save_to_file()
            return jsonify({'success': True, 'config': Config.to_dict()})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    def toggle_system(self):
        """Toggle system enabled/disabled state."""
        Config.ENABLED = not Config.ENABLED
        Config.save_to_file()

        # If disabling, force fan to 0
        if not Config.ENABLED:
            asyncio.run(self.esphome_client.control_fan(0))

        status = "enabled" if Config.ENABLED else "disabled"
        return jsonify({
            'success': True,
            'enabled': Config.ENABLED,
            'message': f'System {status}'
        })

    def force_stop(self):
        """Force fan to stop immediately."""
        asyncio.run(self.esphome_client.control_fan(0))
        LiveData.update(LiveData.current_speed_kmh, 0)
        return jsonify({
            'success': True,
            'message': 'Fan stopped'
        })

    def reconnect(self):
        """Reconnect to ESPHome with current settings."""
        success = self.esphome_client.reconnect()
        return jsonify({
            'success': success,
            'message': 'Connected to ESPHome' if success else 'Failed to connect to ESPHome. Check IP and entity settings.'
        })

    def run(self, host='0.0.0.0', port=5000):
        """
        Run the Flask web server (blocking).

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        print(f"Starting web interface on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

    def run_in_thread(self, host='0.0.0.0', port=5000):
        """
        Run the Flask web server in a separate daemon thread.

        Args:
            host: Host to bind to
            port: Port to bind to

        Returns:
            threading.Thread: The thread running the server
        """
        thread = threading.Thread(
            target=self.run,
            args=(host, port),
            daemon=True
        )
        thread.start()
        return thread

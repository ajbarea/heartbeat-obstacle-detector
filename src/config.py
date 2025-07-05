"""Central configuration for heartbeat obstacle detector system."""

import os

# Heartbeat interval in milliseconds
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "50"))

# Timeout threshold for missing heartbeat in milliseconds
TIMEOUT_THRESHOLD = int(os.getenv("TIMEOUT_THRESHOLD", "500"))

# Host and port for heartbeat communication
HEARTBEAT_HOST = os.getenv("HEARTBEAT_HOST", "localhost")
HEARTBEAT_PORT = int(os.getenv("HEARTBEAT_PORT", "9999"))

# Default duration for monitoring and process manager in seconds
DEFAULT_DURATION = int(os.getenv("DEFAULT_DURATION", "60"))

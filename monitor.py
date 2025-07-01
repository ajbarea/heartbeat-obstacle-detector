# monitor.py listens for heartbeat messages from `detector.py` and restarts
# the detector if heartbeats stop


from datetime import datetime, timezone


def receive_heartbeat(self):
    self.last_heartbeat = datetime.now(timezone.utc)

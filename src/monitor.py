"""Heartbeat-based monitoring and management system for detector processes.

This module implements a robust monitoring system that tracks UDP heartbeat signals
from detector processes and automatically restarts them when heartbeats are missed.
It provides fault tolerance through continuous monitoring and process lifecycle management.
"""

import socket
import time
from datetime import datetime
from typing import List, Optional

from process_manager import ProcessManager


class HeartbeatMonitor:
    """Monitors and manages detector processes via heartbeat signals.

    This class implements a fault-tolerant monitoring system that listens for UDP
    heartbeat messages from detector processes. When heartbeats are missed beyond
    a configured timeout threshold, it automatically restarts the monitored process
    to ensure continuous operation.

    Attributes:
        timeout_threshold (int): Maximum time in milliseconds to wait for heartbeat.
        last_heartbeat (datetime): Timestamp of the last received heartbeat.
        heartbeat_socket (socket.socket): UDP socket for receiving heartbeat messages.
        process_manager (ProcessManager): Manager for the monitored process.
        duration (int): Total monitoring duration in seconds.
        start_time (float): Timestamp when monitoring began.
    """

    # Type annotations for instance attributes
    timeout_threshold: int
    last_heartbeat: Optional[datetime]
    heartbeat_socket: socket.socket
    process_manager: ProcessManager
    duration: int
    start_time: Optional[float]

    def __init__(self, duration: int = 60) -> None:
        """Initialize the heartbeat monitor with specified configuration.

        Sets up the UDP socket for receiving heartbeat messages, configures the
        timeout threshold, and initializes the process manager for handling
        detector process lifecycle operations.

        Args:
            duration (int): Total monitoring duration in seconds. Defaults to 60.
        """
        self.timeout_threshold = 500  # Timeout threshold in milliseconds
        self.last_heartbeat = None
        self.heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heartbeat_socket.bind(("", 9999))
        self.heartbeat_socket.setblocking(False)
        self.process_manager = ProcessManager()
        self.duration = duration
        self.start_time = None

    def start_monitoring(self, cmd: List[str]) -> None:
        """Start the monitoring loop for the detector process.

        Launches the detector process and begins continuous monitoring of heartbeat
        signals. The monitoring loop runs for the specified duration, automatically
        restarting the process when timeouts are detected.

        Args:
            cmd (List[str]): Command and arguments to start the detector process.
        """
        self.process_manager.start_process(cmd)
        self.last_heartbeat = datetime.now()
        self.start_time = time.time()

        while True:
            if time.time() - self.start_time > self.duration:
                print("Monitoring duration reached. Shutting down.")
                # Safely terminate only if worker process exists
                proc = self.process_manager.worker_process
                if proc:
                    self.process_manager.terminate_process(proc)
                break

            self.receive_heartbeat()
            if self.check_timeout():
                print("Heartbeat timeout detected. Restarting process...")
                self.restart_process()
            time.sleep(0.1)

    def receive_heartbeat(self) -> None:
        """Receive and process incoming heartbeat messages.

        Listens for UDP heartbeat messages from the detector process and updates
        the last heartbeat timestamp when a message is successfully received.
        Uses non-blocking socket operations to avoid hanging the monitoring loop.
        """
        try:
            data, addr = self.heartbeat_socket.recvfrom(1024)
            self.last_heartbeat = datetime.now()
            print(f"Heartbeat received at {self.last_heartbeat}")
        except socket.error:
            pass

    def check_timeout(self) -> bool:
        """Check if the heartbeat timeout threshold has been exceeded.

        Calculates the time elapsed since the last heartbeat and compares it
        against the configured timeout threshold to determine if the detector
        process should be considered unresponsive.

        Returns:
            bool: True if the timeout threshold has been exceeded, False otherwise.
        """
        if self.last_heartbeat:
            delta = datetime.now() - self.last_heartbeat
            return (delta.total_seconds() * 1000) > self.timeout_threshold
        return False

    def restart_process(self) -> None:
        """Restart the detector process and reset heartbeat tracking.

        Triggers a complete restart of the detector process through the process
        manager and resets the heartbeat timestamp to begin fresh monitoring.
        This method is called when a heartbeat timeout is detected.
        """
        self.process_manager.restart_process()
        self.last_heartbeat = datetime.now()
        print("Process restarted and heartbeat tracking reset.")


if __name__ == "__main__":
    # Example usage
    monitor = HeartbeatMonitor(duration=10)
    detector_cmd = ["python", "src/detector.py"]
    monitor.start_monitoring(detector_cmd)

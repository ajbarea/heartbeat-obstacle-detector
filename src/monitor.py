"""Heartbeat monitoring system for fault detection.

This module implements a monitor that tracks heartbeat signals from a detector process
and automatically restarts it if heartbeats are missed. It uses UDP sockets for
heartbeat communication and includes process management capabilities.
"""

import socket
import time
from datetime import datetime

from process_manager import ProcessManager


class HeartbeatMonitor:
    """Monitors and manages a detector process using heartbeat-based fault detection.

    This class implements a monitoring system that tracks heartbeat signals from a
    detector process. If heartbeats are not received within the specified timeout
    threshold, it automatically restarts the monitored process.

    Attributes:
        timeout_threshold (int): Maximum time in milliseconds to wait for a heartbeat.
        last_heartbeat (datetime): Timestamp of the most recently received heartbeat.
        heartbeat_socket (socket.socket): UDP socket for receiving heartbeat signals.
        process_manager (ProcessManager): Manager for the monitored process.
        duration (int): Total monitoring duration in seconds.
        start_time (float): Timestamp when monitoring began.
    """

    def __init__(self, duration=60):
        """Initializes the heartbeat monitor with specified duration.

        Args:
            duration (int, optional): Total monitoring duration in seconds. Defaults to 60.
        """
        self.timeout_threshold = 500  # milliseconds
        self.last_heartbeat = None
        self.heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heartbeat_socket.bind(("", 9999))
        self.heartbeat_socket.setblocking(False)
        self.process_manager = ProcessManager()
        self.duration = duration
        self.start_time = None

    def start_monitoring(self, cmd):
        """Initiates the monitoring of a detector process.

        Starts the specified process and monitors its heartbeats until either the
        monitoring duration expires or the process is manually terminated.

        Args:
            cmd (list): Command and arguments to start the detector process.
        """
        self.process_manager.start_process(cmd)
        self.last_heartbeat = datetime.now()
        self.start_time = time.time()

        while True:
            if time.time() - self.start_time > self.duration:
                print("Monitoring duration reached. Shutting down.")
                self.process_manager.terminate_process(
                    self.process_manager.worker_process
                )
                break

            self.receive_heartbeat()
            if self.check_timeout():
                print("Heartbeat timeout detected. Restarting process...")
                self.restart_process()
            time.sleep(0.1)

    def receive_heartbeat(self):
        """Receives and processes incoming heartbeat messages.

        Listens for UDP heartbeat messages from the detector process and updates
        the last heartbeat timestamp when a message is received. Uses non-blocking
        socket operations to prevent hanging.
        """
        try:
            data, addr = self.heartbeat_socket.recvfrom(1024)
            self.last_heartbeat = datetime.now()
            print(f"Heartbeat received at {self.last_heartbeat}")
        except socket.error:
            pass

    def check_timeout(self):
        """Checks if the time since the last heartbeat exceeds the threshold.

        Returns:
            bool: True if the timeout threshold has been exceeded, False otherwise.
        """
        if self.last_heartbeat:
            delta = datetime.now() - self.last_heartbeat
            return (delta.total_seconds() * 1000) > self.timeout_threshold
        return False

    def restart_process(self):
        """Restarts the detector process and resets heartbeat monitoring.

        Triggers a process restart through the process manager and resets the
        heartbeat timestamp to ensure proper monitoring of the new process instance.
        """
        self.process_manager.restart_process()
        self.last_heartbeat = datetime.now()
        print("Process restarted and heartbeat tracking reset.")


if __name__ == "__main__":
    monitor = HeartbeatMonitor(duration=10)  # Run for 10 seconds
    detector_cmd = ["python", "src/detector.py"]
    monitor.start_monitoring(detector_cmd)

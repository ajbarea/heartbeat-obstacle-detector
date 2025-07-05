"""Provide heartbeat-based monitoring and management for a detector process.

Monitors UDP heartbeat signals and restarts the process if signals are missed.
"""

import socket
import time
from datetime import datetime
from typing import List, Optional

from process_manager import ProcessManager


class HeartbeatMonitor:
    """Monitor and manage a detector process via heartbeat signals.

    Attributes:
        timeout_threshold (int): Maximum time in milliseconds to wait for a heartbeat.
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
        """Initialize HeartbeatMonitor.

        Args:
            duration (int): Total monitoring duration in seconds.
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
        """Run the monitoring loop for the detector process.

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
        """Receive and process an incoming heartbeat message.

        Updates last_heartbeat when a message is received.
        """
        try:
            data, addr = self.heartbeat_socket.recvfrom(1024)
            self.last_heartbeat = datetime.now()
            print(f"Heartbeat received at {self.last_heartbeat}")
        except socket.error:
            pass

    def check_timeout(self) -> bool:
        """Check if the time since the last heartbeat exceeds the threshold.

        Returns:
            bool: True if the timeout threshold has been exceeded, False otherwise.
        """
        if self.last_heartbeat:
            delta = datetime.now() - self.last_heartbeat
            return (delta.total_seconds() * 1000) > self.timeout_threshold
        return False

    def restart_process(self) -> None:
        """Restart the detector process and reset heartbeat tracking.

        Triggers a process restart and updates last_heartbeat.
        """
        self.process_manager.restart_process()
        self.last_heartbeat = datetime.now()
        print("Process restarted and heartbeat tracking reset.")


if __name__ == "__main__":
    # Example usage
    monitor = HeartbeatMonitor(duration=10)
    detector_cmd = ["python", "src/detector.py"]
    monitor.start_monitoring(detector_cmd)

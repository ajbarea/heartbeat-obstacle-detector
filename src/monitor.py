"""Heartbeat monitoring service for detector processes.

This module implements a monitoring service that tracks UDP heartbeat signals
from detector processes and coordinates with the ProcessManager for fault recovery.
It focuses specifically on heartbeat detection and timeout management.
"""

import socket
import time
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from process_manager import ProcessManager


class HeartbeatMonitor:
    """Heartbeat monitoring service for detector processes.

    This class implements a monitoring service that listens for UDP heartbeat messages
    from detector processes and coordinates with the ProcessManager for fault recovery.
    It focuses on heartbeat detection and timeout management as a service component.

    Attributes:
        timeout_threshold (int): Maximum time in milliseconds to wait for heartbeat.
        last_heartbeat (datetime): Timestamp of the last received heartbeat.
        heartbeat_socket (socket.socket): UDP socket for receiving heartbeat messages.
        process_manager (ProcessManager): Reference to the main orchestrator.
        duration (int): Total monitoring duration in seconds.
        start_time (float): Timestamp when monitoring began.
    """

    # Type annotations for instance attributes
    timeout_threshold: int
    last_heartbeat: Optional[datetime]
    heartbeat_socket: socket.socket
    process_manager: Optional["ProcessManager"]
    duration: int
    start_time: Optional[float]

    def __init__(self, duration: int = 60) -> None:
        """Initialize the heartbeat monitor service.

        Sets up the UDP socket for receiving heartbeat messages and configures the
        timeout threshold. The ProcessManager reference is set by the orchestrator.

        Args:
            duration (int): Total monitoring duration in seconds. Defaults to 60.
        """
        self.timeout_threshold = 500  # Timeout threshold in milliseconds
        self.last_heartbeat = None
        self.heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heartbeat_socket.bind(("", 9999))
        self.heartbeat_socket.setblocking(False)
        self.process_manager = None  # Set by the orchestrator
        self.duration = duration
        self.start_time = None

    def start_monitoring(self, cmd: List[str]) -> None:
        """Start the monitoring loop for the detector process.

        Launches the detector process via the ProcessManager and begins continuous
        monitoring of heartbeat signals. The monitoring loop runs for the specified
        duration, coordinating with the ProcessManager for fault recovery.

        Args:
            cmd (List[str]): Command and arguments to start the detector process.
        """
        if not self.process_manager:
            raise ValueError(
                "ProcessManager not set. Must be configured by orchestrator."
            )

        self.process_manager.start_process(cmd)
        self.last_heartbeat = datetime.now()
        self.start_time = time.time()

        while True:
            if time.time() - self.start_time > self.duration:
                print("Monitoring duration reached. Shutting down.")
                # Let the ProcessManager handle cleanup
                self.process_manager.shutdown_system()
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
        """Coordinate detector process restart with the ProcessManager.

        Requests the ProcessManager to restart the detector process and resets
        the heartbeat timestamp to begin fresh monitoring. This method is called
        when a heartbeat timeout is detected.
        """
        if self.process_manager:
            self.process_manager.restart_process()
            self.last_heartbeat = datetime.now()
            print("Process restarted and heartbeat tracking reset.")
        else:
            print("Error: ProcessManager not available for restart.")


def main() -> None:
    """Main entry point for standalone monitor usage.

    Note: In the new architecture, the ProcessManager is the main orchestrator.
    For full system orchestration, use the ProcessManager directly.
    """
    print("Warning: Running HeartbeatMonitor in standalone mode.")
    print("For full system orchestration, use 'python src/process_manager.py' instead.")

    # Backward compatibility - create a simple ProcessManager
    from process_manager import ProcessManager

    monitor = HeartbeatMonitor(duration=10)
    manager = ProcessManager(duration=10)
    monitor.process_manager = manager

    detector_cmd = ["python", "src/detector.py"]
    monitor.start_monitoring(detector_cmd)


if __name__ == "__main__":
    main()

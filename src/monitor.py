"""Heartbeat monitoring service for detector processes.

This module implements a monitoring service that tracks UDP heartbeat signals
from detector processes and coordinates with the ProcessManager for fault recovery.
It focuses specifically on heartbeat detection and timeout management.
"""

import socket
import time
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from config import DEFAULT_DURATION, HEARTBEAT_PORT, TIMEOUT_THRESHOLD
from logger import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from process_manager import ProcessManager

logger = get_logger(__name__)


class HeartbeatMonitor:
    """Heartbeat monitoring service for detector processes.

    This class implements a monitoring service that listens for UDP heartbeat messages
    from detector processes and coordinates with the ProcessManager for fault recovery.
    It focuses on heartbeat detection and timeout management as a service component.

    Attributes:
        _timeout_threshold (int): Maximum time in milliseconds to wait for heartbeat.
        _last_heartbeat (datetime): Timestamp of the last received heartbeat.
        _heartbeat_socket (socket.socket): UDP socket for receiving heartbeat messages.
        _process_manager (ProcessManager): Reference to the main orchestrator.
        _duration (int): Total monitoring duration in seconds.
        _start_time (float): Timestamp when monitoring began.
    """

    # Type annotations for instance attributes
    _timeout_threshold: int
    _last_heartbeat: Optional[datetime]
    _heartbeat_socket: socket.socket
    _process_manager: Optional["ProcessManager"]
    _duration: int
    _start_time: Optional[float]

    def __init__(self, duration: int = 60) -> None:
        """Initialize the heartbeat monitor service.

        Sets up the UDP socket for receiving heartbeat messages and configures the
        timeout threshold. The ProcessManager reference is set by the orchestrator.

        Args:
            duration (int): Total monitoring duration in seconds. Defaults to 60.
        """
        self._timeout_threshold = TIMEOUT_THRESHOLD  # Timeout threshold in milliseconds
        self._last_heartbeat = None
        self._heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._heartbeat_socket.bind(("", HEARTBEAT_PORT))
        self._heartbeat_socket.setblocking(False)
        self._process_manager = None
        self._duration = duration or DEFAULT_DURATION
        self._start_time = None

    def start_monitoring(self, cmd: List[str]) -> None:
        """Start the monitoring loop for the detector process.

        Launches the detector process via the ProcessManager and begins continuous
        monitoring of heartbeat signals. The monitoring loop runs for the specified
        duration, coordinating with the ProcessManager for fault recovery.

        Args:
            cmd (List[str]): Command and arguments to start the detector process.
        """
        if not self._process_manager:
            raise ValueError(
                "ProcessManager not set. Must be configured by orchestrator."
            )

        self._process_manager.start_process(cmd)
        self._last_heartbeat = datetime.now()
        self._start_time = time.time()

        while True:
            if time.time() - self._start_time > self._duration:
                logger.info("Monitoring duration reached. Shutting down.")
                self._process_manager.shutdown_system()
                break

            self.receive_heartbeat()
            if self.check_timeout():
                logger.warning("Heartbeat timeout detected. Restarting process...")
                self.restart_process()
            time.sleep(0.1)

    def receive_heartbeat(self) -> None:
        """Receive and process incoming heartbeat messages.

        Listens for UDP heartbeat messages from the detector process and updates
        the last heartbeat timestamp when a message is successfully received.
        Uses non-blocking socket operations to avoid hanging the monitoring loop.
        """
        try:
            _, _ = self._heartbeat_socket.recvfrom(1024)
            self._last_heartbeat = datetime.now()
            logger.info(f"Heartbeat received at {self._last_heartbeat}")
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
        if self._last_heartbeat:
            delta = datetime.now() - self._last_heartbeat
            return (delta.total_seconds() * 1000) > self._timeout_threshold
        return False

    def restart_process(self) -> None:
        """Coordinate detector process restart with the ProcessManager.

        Requests the ProcessManager to restart the detector process and resets
        the heartbeat timestamp to begin fresh monitoring. This method is called
        when a heartbeat timeout is detected.
        """
        if self._process_manager:
            self._process_manager.restart_process()
            self._last_heartbeat = datetime.now()
            logger.info("Process restarted and heartbeat tracking reset.")
        else:
            logger.error("Error: ProcessManager not available for restart.")


def main() -> None:  # pragma: no cover
    """Main entry point for standalone monitor usage.

    Runs a minimal monitoring setup for testing purposes.
    Use process_manager.py for complete system orchestration.
    """
    logger.warning("Warning: Running HeartbeatMonitor in standalone mode.")
    logger.info(
        "Use 'python src/process_manager.py' for complete system orchestration."
    )

    from process_manager import ProcessManager

    monitor = HeartbeatMonitor(duration=10)
    manager = ProcessManager(duration=10)
    monitor._process_manager = manager

    detector_cmd = ["python", "src/detector.py"]
    monitor.start_monitoring(detector_cmd)


if __name__ == "__main__":
    main()

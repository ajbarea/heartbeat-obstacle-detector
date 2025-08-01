"""Orchestrate heartbeat-based obstacle detection system.

This module provides the main entry point and coordination layer for the complete
heartbeat monitoring system, managing the HeartbeatMonitor service and
ObstacleDetector worker process for fault-tolerant obstacle detection.
"""

import subprocess
from typing import Any, List, Optional

from config import DEFAULT_DURATION
from logger import get_logger
from monitor import HeartbeatMonitor

logger = get_logger(__name__)


class ProcessManager:
    """Orchestrate the heartbeat-based obstacle detection system.

    Coordinates all system components including the HeartbeatMonitor service and
    ObstacleDetector worker process, providing centralized control over the entire
    fault-tolerant system lifecycle.

    Attributes:
        _worker_cmd: Command used to start the worker process.
        _worker_process: Reference to the current worker process.
        _monitor: The heartbeat monitoring service instance.
        _duration: Total system runtime duration in seconds.
    """

    _worker_cmd: Optional[List[str]]
    _worker_process: Optional[subprocess.Popen[Any]]
    _monitor: Optional[HeartbeatMonitor]
    _duration: int

    def __init__(self, duration: Optional[int] = None) -> None:
        """Initialize the process manager with optional custom duration.

        Args:
            duration: Total system runtime duration in seconds.
        """
        self._worker_cmd = None
        self._worker_process = None
        self._monitor = None
        self._duration = duration or DEFAULT_DURATION

    def start_process(self, cmd: List[str]) -> subprocess.Popen[Any]:
        """Launch a new worker process.

        Args:
            cmd: Command and arguments to start the worker process.

        Returns:
            Reference to the started worker process.
        """
        logger.info(f"Starting worker process with command: {' '.join(cmd)}")
        self._worker_cmd = cmd
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self._worker_process = proc
        return proc

    def restart_process(self) -> subprocess.Popen[Any]:
        """Restart the worker process with the stored command.

        Returns:
            Reference to the new worker process.

        Raises:
            ValueError: If no command was previously stored via start_process().
        """
        if not self._worker_cmd:
            raise ValueError("No command stored. Call start_process() first.")

        if self._worker_process and self.is_process_running():
            logger.info("Terminating existing worker process...")
            self.terminate_process(self._worker_process)

        logger.info(
            f"Restarting worker process with command: {' '.join(self._worker_cmd)}"
        )
        proc = subprocess.Popen(
            self._worker_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self._worker_process = proc
        return proc

    def terminate_process(self, proc: subprocess.Popen[Any]) -> None:
        """Gracefully terminate a process with proper cleanup.

        Attempts graceful termination first, then forces termination if the process
        doesn't exit within the timeout period. Uses safe process termination to
        avoid PID reuse attacks and race conditions.

        Args:
            proc: Process to terminate.
        """
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    pass

    def is_process_running(self) -> bool:
        """Check if the worker process is currently running.

        Returns:
            True if the worker process exists and is running, False otherwise.
        """
        if not self._worker_process:
            return False
        return self._worker_process.poll() is None

    def start_system(self, detector_cmd: List[str]) -> None:
        """Start the complete heartbeat monitoring system.

        Initializes and starts both the HeartbeatMonitor service and the
        ObstacleDetector worker process.

        Args:
            detector_cmd: Command and arguments for the detector process.
        """
        logger.info("Starting heartbeat monitoring system...")
        logger.info(f"System duration: {self._duration} seconds")

        self._monitor = HeartbeatMonitor(duration=self._duration)
        self._monitor._process_manager = self
        self._monitor.start_monitoring(detector_cmd)

        logger.info("System shutdown completed.")

    def shutdown_system(self) -> None:
        """Gracefully shutdown the entire monitoring system.

        Terminates all running processes and cleans up resources in the
        correct order to ensure proper system shutdown.
        """
        logger.info("Shutting down system...")

        if self._worker_process and self.is_process_running():
            logger.info("Terminating detector process...")
            self.terminate_process(self._worker_process)

        if self._monitor and hasattr(self._monitor, "_heartbeat_socket"):
            logger.info("Closing monitor socket...")
            self._monitor._heartbeat_socket.close()

        logger.info("System shutdown completed.")


def main() -> None:  # pragma: no cover
    """Main entry point for the heartbeat monitoring system."""
    import sys

    duration = 60
    detector_cmd = ["python", "src/detector.py"]

    # Parse command line arguments for duration
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
            logger.info(f"Using custom duration: {duration} seconds")
        except ValueError:
            logger.warning(
                f"Invalid duration '{sys.argv[1]}', using default: {duration} seconds"
            )

    manager = ProcessManager(duration=duration)

    try:
        manager.start_system(detector_cmd)
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal...")
        manager.shutdown_system()
    except Exception as e:
        logger.error(f"System error: {e}")
        manager.shutdown_system()
        sys.exit(1)


if __name__ == "__main__":
    main()

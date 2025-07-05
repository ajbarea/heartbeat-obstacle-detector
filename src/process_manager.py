"""Orchestrate heartbeat-based obstacle detection system.

This module provides the main entry point and coordination layer for the complete
heartbeat monitoring system, managing the HeartbeatMonitor service and
ObstacleDetector worker process for fault-tolerant obstacle detection.
"""

import os
import signal
import subprocess
from typing import Any, List, Optional

from monitor import HeartbeatMonitor


class ProcessManager:
    """Orchestrate the heartbeat-based obstacle detection system.

    Coordinates all system components including the HeartbeatMonitor service and
    ObstacleDetector worker process, providing centralized control over the entire
    fault-tolerant system lifecycle.

    Attributes:
        worker_cmd: Command used to start the worker process.
        worker_process: Reference to the current worker process.
        monitor: The heartbeat monitoring service instance.
        duration: Total system runtime duration in seconds.
    """

    worker_cmd: Optional[List[str]]
    worker_process: Optional[subprocess.Popen[Any]]
    monitor: Optional[HeartbeatMonitor]
    duration: int

    def __init__(self, duration: int = 60) -> None:
        """Initialize the process manager.

        Args:
            duration: Total system runtime duration in seconds.
        """
        self.worker_cmd = None
        self.worker_process = None
        self.monitor = None
        self.duration = duration

    def start_process(self, cmd: List[str]) -> subprocess.Popen[Any]:
        """Launch a new worker process.

        Args:
            cmd: Command and arguments to start the worker process.

        Returns:
            Reference to the started worker process.
        """
        print(f"Starting worker process with command: {' '.join(cmd)}")
        self.worker_cmd = cmd
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.worker_process = proc
        return proc

    def restart_process(self) -> subprocess.Popen[Any]:
        """Restart the worker process with the stored command.

        Returns:
            Reference to the new worker process.

        Raises:
            ValueError: If no command was previously stored via start_process().
        """
        if not self.worker_cmd:
            raise ValueError("No command stored. Call start_process() first.")

        if self.worker_process and self.is_process_running():
            print("Terminating existing worker process...")
            self.terminate_process(self.worker_process)

        print(f"Restarting worker process with command: {' '.join(self.worker_cmd)}")
        proc = subprocess.Popen(
            self.worker_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.worker_process = proc
        return proc

    def terminate_process(self, proc: subprocess.Popen[Any]) -> None:
        """Gracefully terminate a process with proper cleanup.

        Attempts graceful termination first, then forces termination if the process
        doesn't exit within the timeout period.

        Args:
            proc: Process to terminate.
        """
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    # Use SIGKILL on Unix-like systems for forceful termination
                    if hasattr(signal, "SIGKILL"):
                        os.kill(proc.pid, getattr(signal, "SIGKILL"))
                    else:
                        # Fallback for Windows systems
                        os.kill(proc.pid, signal.SIGTERM)
                except OSError:
                    # Process already terminated - ignore race condition
                    pass

    def is_process_running(self) -> bool:
        """Check if the worker process is currently running.

        Returns:
            True if the worker process exists and is running, False otherwise.
        """
        if not self.worker_process:
            return False
        return self.worker_process.poll() is None

    def start_system(self, detector_cmd: List[str]) -> None:
        """Start the complete heartbeat monitoring system.

        Initializes and starts both the HeartbeatMonitor service and the
        ObstacleDetector worker process.

        Args:
            detector_cmd: Command and arguments for the detector process.
        """
        print("Starting heartbeat monitoring system...")
        print(f"System duration: {self.duration} seconds")

        self.monitor = HeartbeatMonitor(duration=self.duration)
        self.monitor.process_manager = self
        self.monitor.start_monitoring(detector_cmd)

        print("System shutdown completed.")

    def shutdown_system(self) -> None:
        """Gracefully shutdown the entire monitoring system.

        Terminates all running processes and cleans up resources in the
        correct order to ensure proper system shutdown.
        """
        print("Shutting down system...")

        if self.worker_process and self.is_process_running():
            print("Terminating detector process...")
            self.terminate_process(self.worker_process)

        if self.monitor and hasattr(self.monitor, "heartbeat_socket"):
            print("Closing monitor socket...")
            self.monitor.heartbeat_socket.close()

        print("System shutdown completed.")


def main() -> None:  # pragma: no cover
    """Main entry point for the heartbeat monitoring system."""
    import sys

    duration = 60
    detector_cmd = ["python", "src/detector.py"]

    # Parse command line arguments for duration
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
            print(f"Using custom duration: {duration} seconds")
        except ValueError:
            print(
                f"Invalid duration '{sys.argv[1]}', using default: {duration} seconds"
            )

    manager = ProcessManager(duration=duration)

    try:
        manager.start_system(detector_cmd)
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
        manager.shutdown_system()
    except Exception as e:
        print(f"System error: {e}")
        manager.shutdown_system()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Main orchestration system for heartbeat-based obstacle detection.

This module serves as the primary entry point and orchestrator for the entire
heartbeat monitoring system. It coordinates the HeartbeatMonitor service and
ObstacleDetector worker process to provide fault-tolerant obstacle detection.
"""

import os
import signal
import subprocess
from typing import Any, List, Optional

from monitor import HeartbeatMonitor


class ProcessManager:
    """Main orchestrator for the heartbeat-based obstacle detection system.

    This class serves as the primary entry point and coordinates all system components.
    It manages both the HeartbeatMonitor service and ObstacleDetector worker process,
    providing centralized control over the entire fault-tolerant system.

    Attributes:
        worker_cmd (list): The command used to start the worker process.
        worker_process (subprocess.Popen): Reference to the current worker process.
        monitor (HeartbeatMonitor): The heartbeat monitoring service.
        duration (int): Total system runtime duration in seconds.
    """

    worker_cmd: Optional[List[str]]
    worker_process: Optional[subprocess.Popen[Any]]
    monitor: Optional[HeartbeatMonitor]
    duration: int

    def __init__(self, duration: int = 60) -> None:
        """Initialize the process manager as the main system orchestrator.

        Creates a new process manager instance that will coordinate the entire
        heartbeat monitoring system including the monitor service and detector worker.

        Args:
            duration (int): Total system runtime duration in seconds. Defaults to 60.
        """
        self.worker_cmd = None
        self.worker_process = None
        self.monitor = None
        self.duration = duration

    def start_process(self, cmd: List[str]) -> subprocess.Popen:
        """Launch a new worker process with the specified command.

        Creates and starts a new subprocess using the provided command and arguments.
        The process is configured to run without displaying output to keep the
        monitoring system clean.

        Args:
            cmd (list): Command and arguments to start the worker process.

        Returns:
            subprocess.Popen: Reference to the started worker process.
        """
        print(f"Starting worker process with command: {' '.join(cmd)}")
        self.worker_cmd = cmd
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.worker_process = proc
        return proc

    def restart_process(self) -> subprocess.Popen:
        """Restart the worker process with the stored command.

        Terminates the current worker process if it's running and launches a new
        instance using the previously stored command. This ensures a clean restart
        with the same configuration.

        Returns:
            subprocess.Popen: Reference to the new worker process.

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

    def terminate_process(self, proc: subprocess.Popen) -> None:
        """Gracefully terminate a process with proper cleanup.

        Attempts graceful termination first using SIGTERM, then waits for the
        process to exit cleanly. If the process doesn't terminate within the
        timeout period, it forces termination to prevent hanging.

        Args:
            proc (subprocess.Popen): Process to terminate.
        """
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
            except subprocess.TimeoutExpired:
                # Force termination if graceful shutdown fails
                os.kill(proc.pid, signal.SIGTERM)

    def is_process_running(self) -> bool:
        """Check if the worker process is currently running.

        Verifies that the worker process exists and is still active by checking
        its process state. This method is used to determine if process management
        actions are needed.

        Returns:
            bool: True if the worker process exists and is running, False otherwise.
        """
        if not self.worker_process:
            return False
        return self.worker_process.poll() is None

    def start_system(self, detector_cmd: List[str]) -> None:
        """Start the complete heartbeat monitoring system.

        Initializes and starts both the HeartbeatMonitor service and the
        ObstacleDetector worker process. This is the main entry point for
        the entire system.

        Args:
            detector_cmd (List[str]): Command and arguments for the detector process.
        """
        print("Starting heartbeat monitoring system...")
        print(f"System duration: {self.duration} seconds")

        # Create and configure the monitor service
        self.monitor = HeartbeatMonitor(duration=self.duration)

        # Set the process manager reference in the monitor
        self.monitor.process_manager = self

        # Start the monitoring system
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


def main() -> None:
    """Main entry point for the heartbeat monitoring system.

    Creates and starts the complete system with default configuration.
    """
    import sys

    # Default configuration
    duration = 60
    detector_cmd = ["python", "src/detector.py"]

    # Parse command line arguments for duration if provided
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
            print(f"Using custom duration: {duration} seconds")
        except ValueError:
            print(
                f"Invalid duration '{sys.argv[1]}', using default: {duration} seconds"
            )

    # Create and start the system
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

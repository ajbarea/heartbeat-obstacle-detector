"""Process management system for worker processes.

This module provides functionality for launching, monitoring, and managing worker
processes. It handles process lifecycle operations including starting, restarting,
and graceful termination with proper cleanup.
"""

import os
import signal
import subprocess
from typing import Any, List, Optional


class ProcessManager:
    """Manages the lifecycle of worker processes

    This class provides methods to start, restart, and terminate worker processes
    while maintaining process state and command information.

    Attributes:
        worker_cmd (list): The command used to start the worker process.
        worker_process (subprocess.Popen): Reference to the current worker process.
    """

    worker_cmd: Optional[List[str]]
    worker_process: Optional[subprocess.Popen[Any]]

    def __init__(self) -> None:
        """Initializes a new process manager with no active worker."""
        self.worker_cmd = None
        self.worker_process = None

    def start_process(self, cmd: List[str]) -> subprocess.Popen:
        """Launches a new worker process.

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
        """Restarts the worker process.

        Terminates the current worker process if it's running and starts a new
        instance using the stored command.

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
        """Gracefully terminates a process with cleanup.

        Attempts graceful termination first, then forcefully terminates if the
        process doesn't exit within the timeout period.

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
        """Checks if the worker process is currently running.

        Returns:
            bool: True if the worker process exists and is running, False otherwise.
        """
        if not self.worker_process:
            return False
        return self.worker_process.poll() is None

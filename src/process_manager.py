# handles launching and restarting processes
import os
import signal
import subprocess


class ProcessManager:
    def __init__(self):
        # Store the command used to start worker process
        self.worker_cmd = None
        # Reference to the current worker process
        self.worker_process = None

    def start_process(self, cmd):
        # Launch new worker process using subprocess
        # Store process reference and command
        # Return the process object
        pass

    def restart_process(self, cmd):
        # Terminate current worker process if running
        # Start new worker process with same command
        # Update process reference
        # Return new process object
        pass

    def terminate_process(self, proc):
        # Gracefully terminate the given process
        # Handle process cleanup
        # Wait for process to fully terminate
        pass

    def is_process_running(self):
        # Check if worker process is still alive
        # Return True if running, False if terminated/crashed
        pass

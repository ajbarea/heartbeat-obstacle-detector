"""Unit tests for the ProcessManager class.

This module contains comprehensive unit tests for the process management system,
covering process lifecycle operations, error handling, and state management
with proper mocking and validation.
"""

import subprocess
from unittest.mock import Mock, call, patch

import pytest

from src.process_manager import ProcessManager


@pytest.fixture
def process_manager():
    """Create and return a ProcessManager instance for testing.

    Returns:
        ProcessManager: A new ProcessManager instance with clean state.
    """
    return ProcessManager()


@pytest.fixture
def mock_process():
    """Create a mock subprocess.Popen instance with a running state.

    Returns:
        Mock: A mock Popen process configured to simulate a running process.
    """
    mock_proc = Mock(spec=subprocess.Popen)
    mock_proc.poll.return_value = None
    mock_proc.pid = 12345
    return mock_proc


def test_initialization(process_manager):
    """Verify that a new ProcessManager has no worker command or process.

    Tests that the ProcessManager initializes with clean state and no
    active worker processes or stored commands.

    Args:
        process_manager (ProcessManager): Fixture providing a clean manager.
    """
    assert process_manager.worker_cmd is None
    assert process_manager.worker_process is None
    assert process_manager.monitor is None
    assert process_manager.duration == 60


@patch("subprocess.Popen")
@patch("src.process_manager.logger")
def test_start_process(mock_logger, mock_popen, process_manager, mock_process):
    """Start a worker process with the given command and verify setup.

    Tests that the process manager correctly starts a new worker process
    with the specified command and properly stores the process reference.

    Args:
        mock_logger (Mock): Mock for logger.
        mock_popen (Mock): Mock for subprocess.Popen.
        process_manager (ProcessManager): Fixture providing a manager.
        mock_process (Mock): Fixture providing a mock Popen process.

    Returns:
        subprocess.Popen: The mock process returned by start_process.
    """
    mock_popen.return_value = mock_process
    cmd = ["python", "worker.py"]

    result = process_manager.start_process(cmd)

    assert process_manager.worker_cmd == cmd
    assert process_manager.worker_process == mock_process
    assert result == mock_process
    mock_popen.assert_called_once_with(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    mock_logger.info.assert_called_once_with(
        "Starting worker process with command: python worker.py"
    )


@pytest.mark.parametrize(
    "cmd,expected_message",
    [
        (
            ["python", "script.py"],
            "Starting worker process with command: python script.py",
        ),
        (
            ["java", "-jar", "app.jar"],
            "Starting worker process with command: java -jar app.jar",
        ),
        (
            ["node", "app.js", "--port", "3000"],
            "Starting worker process with command: node app.js --port 3000",
        ),
    ],
)
@patch("subprocess.Popen")
@patch("src.process_manager.logger")
def test_start_process_with_various_commands(
    mock_logger, mock_popen, process_manager, mock_process, cmd, expected_message
):
    """Verify start_process logs correct messages for various command formats.

    Tests that the process manager correctly formats and logs command
    information when starting processes with different argument structures.

    Args:
        mock_logger (Mock): Mock for logger.
        mock_popen (Mock): Mock for subprocess.Popen.
        process_manager (ProcessManager): Fixture providing a manager.
        mock_process (Mock): Fixture providing a mock Popen process.
        cmd (list): Command list to pass to start_process.
        expected_message (str): Expected output message.
    """
    mock_popen.return_value = mock_process

    process_manager.start_process(cmd)

    mock_logger.info.assert_called_once_with(expected_message)


def test_restart_process_no_command_stored(process_manager):
    """Verify restart_process raises ValueError when no command is stored.

    Tests that attempting to restart a process without first calling
    start_process raises the appropriate error with a clear message.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    with pytest.raises(
        ValueError, match=r"No command stored. Call start_process\(\) first."
    ):
        process_manager.restart_process()


@patch("subprocess.Popen")
@patch("src.process_manager.logger")
def test_restart_process_no_existing_process(
    mock_logger, mock_popen, process_manager, mock_process
):
    """Restart process when no existing process is running and verify new process start.

    Tests that the process manager correctly handles restart operations
    when no existing process is currently running.

    Args:
        mock_logger (Mock): Mock for logger.
        mock_popen (Mock): Mock for subprocess.Popen.
        process_manager (ProcessManager): Fixture providing a manager.
        mock_process (Mock): Fixture providing a mock Popen process.

    Returns:
        subprocess.Popen: The newly started mock process.
    """
    mock_popen.return_value = mock_process
    process_manager.worker_cmd = ["python", "worker.py"]
    process_manager.worker_process = None

    result = process_manager.restart_process()

    assert result == mock_process
    assert process_manager.worker_process == mock_process
    mock_popen.assert_called_once_with(
        ["python", "worker.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    mock_logger.info.assert_called_once_with(
        "Restarting worker process with command: python worker.py"
    )


@patch("subprocess.Popen")
@patch("src.process_manager.logger")
def test_restart_process_with_running_process(mock_logger, mock_popen, process_manager):
    """Terminate a running process and restart it, verifying termination and restart logic.

    Tests that the process manager correctly handles restart operations
    when an existing process is currently running, ensuring proper cleanup.

    Args:
        mock_logger (Mock): Mock for logger.
        mock_popen (Mock): Mock for subprocess.Popen.
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_old_process = Mock()
    mock_old_process.poll.return_value = None
    mock_old_process.pid = 12345

    mock_new_process = Mock()
    mock_popen.return_value = mock_new_process

    process_manager.worker_cmd = ["python", "worker.py"]
    process_manager.worker_process = mock_old_process

    with patch.object(
        process_manager, "is_process_running", return_value=True
    ), patch.object(process_manager, "terminate_process") as mock_terminate:
        result = process_manager.restart_process()

        assert result == mock_new_process
        assert process_manager.worker_process == mock_new_process
        mock_terminate.assert_called_once_with(mock_old_process)
        mock_logger.info.assert_any_call("Terminating existing worker process...")
        mock_logger.info.assert_any_call(
            "Restarting worker process with command: python worker.py"
        )


@pytest.mark.parametrize(
    "poll_return,expected_result",
    [
        (None, True),
        (0, False),
        (1, False),
        (-1, False),
    ],
)
def test_is_process_running(
    process_manager, mock_process, poll_return, expected_result
):
    """Verify is_process_running returns correct boolean based on process poll state.

    Tests that the process running check correctly interprets the poll result
    to determine if a process is still active.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
        mock_process (Mock): Fixture providing a mock Popen process.
        poll_return (Optional[int]): The return value from poll().
        expected_result (bool): Expected result from is_process_running().
    """
    mock_process.poll.return_value = poll_return
    process_manager.worker_process = mock_process

    result = process_manager.is_process_running()

    assert result == expected_result
    mock_process.poll.assert_called_once()


def test_is_process_running_no_process(process_manager):
    """Verify is_process_running returns False when no process is set.

    Tests that the process running check correctly handles the case
    when no worker process has been assigned.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    process_manager.worker_process = None

    result = process_manager.is_process_running()

    assert result is False


def test_terminate_process_already_terminated(process_manager):
    """Verify terminate_process does nothing when the process is already terminated.

    Tests that the termination logic correctly handles processes that have
    already exited and avoids unnecessary termination attempts.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_process = Mock()
    mock_process.poll.return_value = 0

    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_not_called()
    mock_process.wait.assert_not_called()


def test_terminate_process_graceful_shutdown(process_manager):
    """Test terminate_process with successful graceful shutdown.

    Verifies that the process termination correctly handles graceful
    shutdown scenarios where the process exits cleanly.
    """
    mock_process = Mock()
    mock_process.poll.return_value = None  # Process is running
    mock_process.wait.return_value = 0  # Graceful shutdown

    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once_with(timeout=5)


def test_terminate_process_forced_shutdown(process_manager):
    """Verify terminate_process forces shutdown if graceful termination times out.

    Tests that the process termination correctly handles timeout scenarios
    by forcing process termination when graceful shutdown fails.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = [
        subprocess.TimeoutExpired(cmd="test", timeout=5),
        None,  # Second call succeeds after kill()
    ]
    mock_process.pid = 12345

    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    # Should call wait twice: once with timeout=5, then once with timeout=2
    expected_calls = [call(timeout=5), call(timeout=2)]
    mock_process.wait.assert_has_calls(expected_calls)
    # Should call kill() when graceful termination times out
    mock_process.kill.assert_called_once()


def test_terminate_process_forced_shutdown_with_sigkill(process_manager):
    """Verify terminate_process uses proc.kill() for safe forceful termination.

    Tests that the process termination correctly uses subprocess.kill() for safer
    forceful termination instead of os.kill().

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = [
        subprocess.TimeoutExpired(cmd="test", timeout=5),
        None,  # Second call succeeds after kill()
    ]
    mock_process.pid = 12345

    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    # Should call wait twice: once with timeout=5, then once with timeout=2
    expected_calls = [call(timeout=5), call(timeout=2)]
    mock_process.wait.assert_has_calls(expected_calls)
    # Should call kill() when graceful termination times out
    mock_process.kill.assert_called_once()


def test_terminate_process_handles_process_lookup_error(process_manager):
    """Verify terminate_process handles OSError gracefully during kill().

    Tests that the process termination handles race conditions where the process
    terminates between timeout and kill signal, raising OSError.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
    mock_process.kill.side_effect = OSError("No such process")
    mock_process.pid = 12345

    # This should not raise an exception
    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once_with(timeout=5)
    mock_process.kill.assert_called_once()


def test_terminate_process_handles_os_error(process_manager):
    """Verify terminate_process handles OSError gracefully.

    Tests that the process termination handles OS-level errors (like permission
    denied) when trying to send kill signals.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
    mock_process.kill.side_effect = OSError("Operation not permitted")
    mock_process.pid = 12345

    # This should not raise an exception
    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once_with(timeout=5)
    mock_process.kill.assert_called_once()


def test_terminate_process_handles_timeout_after_kill(process_manager):
    """Verify terminate_process handles TimeoutExpired during second wait().

    Tests that the process termination handles cases where the process doesn't
    terminate even after kill() is called, and the second wait() times out.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = [
        subprocess.TimeoutExpired(cmd="test", timeout=5),
        subprocess.TimeoutExpired(cmd="test", timeout=2),  # Second wait also times out
    ]
    mock_process.pid = 12345

    # This should not raise an exception
    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    # Should call wait twice: once with timeout=5, then once with timeout=2
    expected_calls = [call(timeout=5), call(timeout=2)]
    mock_process.wait.assert_has_calls(expected_calls)
    mock_process.kill.assert_called_once()


class TestProcessManagerIntegration:
    """Integration tests for ProcessManager workflow scenarios.

    This class contains integration tests that verify the complete process
    management workflows including start, restart, and termination sequences.
    """

    @pytest.fixture
    def manager(self):
        """Create and return a ProcessManager instance for integration tests.

        Returns:
            ProcessManager: A new ProcessManager instance for integration testing.
        """
        return ProcessManager()

    @patch("subprocess.Popen")
    @patch("src.process_manager.logger")
    def test_full_lifecycle(self, mock_logger, mock_popen, manager):
        """Test the complete lifecycle: start -> restart -> terminate.

        Verifies that the process manager correctly handles a complete
        process lifecycle including initial start, restart, and termination.

        Args:
            mock_logger (Mock): Mock for logger.
            mock_popen (Mock): Mock for subprocess.Popen.
            manager (ProcessManager): Fixture providing a manager.
        """
        # Setup mock processes
        mock_process1 = Mock()
        mock_process1.poll.return_value = None
        mock_process1.pid = 12345

        mock_process2 = Mock()
        mock_process2.poll.return_value = None
        mock_process2.pid = 67890

        mock_popen.side_effect = [mock_process1, mock_process2]

        cmd = ["python", "worker.py"]

        # Start process
        result1 = manager.start_process(cmd)
        assert result1 == mock_process1
        assert manager.worker_process == mock_process1
        assert manager.worker_cmd == cmd

        # Restart process
        with patch.object(manager, "terminate_process") as mock_terminate:
            result2 = manager.restart_process()
            assert result2 == mock_process2
            assert manager.worker_process == mock_process2
            mock_terminate.assert_called_once_with(mock_process1)

        # Verify log calls
        assert mock_logger.info.call_count == 3
        mock_logger.info.assert_any_call(
            "Starting worker process with command: python worker.py"
        )
        mock_logger.info.assert_any_call("Terminating existing worker process...")
        mock_logger.info.assert_any_call(
            "Restarting worker process with command: python worker.py"
        )

    def test_error_handling_workflow(self, manager):
        """Test error handling for restart without start, is_process_running, and terminate with None.

        Verifies that the process manager correctly handles error conditions
        and edge cases in various workflow scenarios.

        Args:
            manager (ProcessManager): Fixture providing a manager.
        """
        # Test restart without start
        with pytest.raises(ValueError):
            manager.restart_process()

        # Test is_process_running with no process
        assert manager.is_process_running() is False

        # Test terminate with None process (should not crash)
        manager.worker_process = None
        assert manager.is_process_running() is False


@patch("src.process_manager.logger")
def test_start_system(mock_logger, process_manager):
    """Test the start_system method coordinates the entire system.

    Verifies that start_system properly sets up the monitor and
    delegates to the monitor's start_monitoring method.

    Args:
        mock_logger (Mock): Mock for logger.
        process_manager (ProcessManager): Fixture providing a manager.
    """
    detector_cmd = ["python", "src/detector.py"]

    with patch("src.process_manager.HeartbeatMonitor") as mock_monitor_class:
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor

        process_manager.start_system(detector_cmd)

        # Verify monitor was created and configured
        mock_monitor_class.assert_called_once_with(duration=60)
        assert process_manager.monitor == mock_monitor
        assert mock_monitor.process_manager == process_manager

        # Verify start_monitoring was called
        mock_monitor.start_monitoring.assert_called_once_with(detector_cmd)


@patch("src.process_manager.logger")
def test_shutdown_system(mock_logger, process_manager):
    """Test the shutdown_system method handles cleanup properly.

    Verifies that shutdown_system terminates processes and closes sockets.

    Args:
        mock_logger (Mock): Mock for logger.
        process_manager (ProcessManager): Fixture providing a manager.
    """
    # Set up mock worker process
    mock_worker = Mock()
    mock_worker.poll.return_value = None  # Process is running
    process_manager.worker_process = mock_worker

    # Set up mock monitor
    mock_monitor = Mock()
    mock_socket = Mock()
    mock_monitor.heartbeat_socket = mock_socket
    process_manager.monitor = mock_monitor

    with patch.object(process_manager, "terminate_process") as mock_terminate:
        process_manager.shutdown_system()

        # Verify process was terminated
        mock_terminate.assert_called_once_with(mock_worker)

        # Verify socket was closed
        mock_socket.close.assert_called_once()


@patch("src.process_manager.logger")
def test_shutdown_system_no_worker(mock_logger, process_manager):
    """Test shutdown_system when no worker process exists.

    Verifies that shutdown_system handles the case where no worker
    process is running without errors.

    Args:
        mock_logger (Mock): Mock for logger.
        process_manager (ProcessManager): Fixture providing a manager.
    """
    # Set up mock monitor without worker
    mock_monitor = Mock()
    mock_socket = Mock()
    mock_monitor.heartbeat_socket = mock_socket
    process_manager.monitor = mock_monitor
    process_manager.worker_process = None

    with patch.object(process_manager, "terminate_process") as mock_terminate:
        process_manager.shutdown_system()

        # Verify terminate was not called since no worker
        mock_terminate.assert_not_called()

        # Verify socket was still closed
        mock_socket.close.assert_called_once()


@patch("src.process_manager.logger")
def test_shutdown_system_no_monitor(mock_logger, process_manager):
    """Test shutdown_system when no monitor exists.

    Verifies that shutdown_system handles the case where no monitor
    has been set up without errors.

    Args:
        mock_logger (Mock): Mock for logger.
        process_manager (ProcessManager): Fixture providing a manager.
    """
    # Set up mock worker process only
    mock_worker = Mock()
    mock_worker.poll.return_value = None  # Process is running
    process_manager.worker_process = mock_worker
    process_manager.monitor = None

    with patch.object(process_manager, "terminate_process") as mock_terminate:
        process_manager.shutdown_system()

        # Verify process was terminated
        mock_terminate.assert_called_once_with(mock_worker)

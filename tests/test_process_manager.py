"""Unit tests for the ProcessManager class.

These tests cover process lifecycle operations, error handling, and state management.
"""

import signal
import subprocess
from unittest.mock import Mock, patch

import pytest

from src.process_manager import ProcessManager


@pytest.fixture
def process_manager():
    """Create and return a ProcessManager instance for testing.

    Returns:
        ProcessManager: A new ProcessManager instance.
    """
    return ProcessManager()


@pytest.fixture
def mock_process():
    """Create a mock subprocess.Popen instance with a running state.

    Returns:
        Mock: A mock Popen process with a running state.
    """
    mock_proc = Mock(spec=subprocess.Popen)
    mock_proc.poll.return_value = None
    mock_proc.pid = 12345
    return mock_proc


def test_initialization(process_manager):
    """Verify that a new ProcessManager has no worker command or process.

    Args:
        process_manager (ProcessManager): Fixture providing a clean manager.
    """
    assert process_manager.worker_cmd is None
    assert process_manager.worker_process is None


@patch("subprocess.Popen")
@patch("builtins.print")
def test_start_process(mock_print, mock_popen, process_manager, mock_process):
    """Start a worker process with the given command and verify Popen invocation and print output.

    Args:
        mock_print (Mock): Mock for builtins.print.
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
    mock_print.assert_called_once_with(
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
@patch("builtins.print")
def test_start_process_with_various_commands(
    mock_print, mock_popen, process_manager, mock_process, cmd, expected_message
):
    """Verify start_process prints the correct message for various command formats.

    Args:
        mock_print (Mock): Mock for builtins.print.
        mock_popen (Mock): Mock for subprocess.Popen.
        process_manager (ProcessManager): Fixture providing a manager.
        mock_process (Mock): Fixture providing a mock Popen process.
        cmd (list): Command list to pass to start_process.
        expected_message (str): Expected output message.
    """
    mock_popen.return_value = mock_process

    process_manager.start_process(cmd)

    mock_print.assert_called_once_with(expected_message)


def test_restart_process_no_command_stored(process_manager):
    """Verify restart_process raises a ValueError when no command is stored.

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    with pytest.raises(
        ValueError, match=r"No command stored. Call start_process\(\) first."
    ):
        process_manager.restart_process()


@patch("subprocess.Popen")
@patch("builtins.print")
def test_restart_process_no_existing_process(
    mock_print, mock_popen, process_manager, mock_process
):
    """Restart process when no existing process is running and verify new process start.

    Args:
        mock_print (Mock): Mock for builtins.print.
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
    mock_print.assert_called_once_with(
        "Restarting worker process with command: python worker.py"
    )


@patch("subprocess.Popen")
@patch("builtins.print")
def test_restart_process_with_running_process(mock_print, mock_popen, process_manager):
    """Terminate a running process and restart it, verifying termination and restart logic.

    Args:
        mock_print (Mock): Mock for builtins.print.
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
        mock_print.assert_any_call("Terminating existing worker process...")
        mock_print.assert_any_call(
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

    Args:
        process_manager (ProcessManager): Fixture providing a manager.
    """
    process_manager.worker_process = None

    result = process_manager.is_process_running()

    assert result is False


def test_terminate_process_already_terminated(process_manager):
    """Verify terminate_process does nothing when the process is already terminated.

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
    """Test terminate_process with successful graceful shutdown."""
    mock_process = Mock()
    mock_process.poll.return_value = None  # Process is running
    mock_process.wait.return_value = 0  # Graceful shutdown

    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once_with(timeout=5)


@patch("os.kill")
def test_terminate_process_forced_shutdown(mock_kill, process_manager):
    """Verify terminate_process forces shutdown if graceful termination times out.

    Args:
        mock_kill (Callable): Mock for os.kill.
        process_manager (ProcessManager): Fixture providing a manager.
    """
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
    mock_process.pid = 12345

    process_manager.terminate_process(mock_process)

    mock_process.poll.assert_called_once()
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once_with(timeout=5)
    mock_kill.assert_called_once_with(12345, signal.SIGTERM)


class TestProcessManagerIntegration:
    """Integration tests for ProcessManager workflow scenarios."""

    @pytest.fixture
    def manager(self):
        """Create and return a ProcessManager instance for integration tests.

        Returns:
            ProcessManager: A new ProcessManager instance.
        """
        return ProcessManager()

    @patch("subprocess.Popen")
    @patch("builtins.print")
    def test_full_lifecycle(self, mock_print, mock_popen, manager):
        """Test the complete lifecycle: start -> restart -> terminate.

        Args:
            mock_print (Mock): Mock for builtins.print.
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

        # Verify print calls
        assert mock_print.call_count == 3
        mock_print.assert_any_call(
            "Starting worker process with command: python worker.py"
        )
        mock_print.assert_any_call("Terminating existing worker process...")
        mock_print.assert_any_call(
            "Restarting worker process with command: python worker.py"
        )

    def test_error_handling_workflow(self, manager):
        """Test error handling for restart without start, is_process_running, and terminate with None.

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

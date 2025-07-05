"""Test suite for the HeartbeatMonitor class.

This module contains comprehensive unit tests for the heartbeat monitoring system,
including heartbeat reception, timeout detection, process management, and monitoring
lifecycle operations.
"""

import socket
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.monitor import HeartbeatMonitor


@pytest.fixture
def mock_socket():
    """Create a mock socket for testing.

    Returns:
        Mock: Mock socket instance with common socket methods.
    """
    mock_sock = Mock(spec=socket.socket)
    return mock_sock


@pytest.fixture
def mock_process_manager():
    """Create a mock ProcessManager for testing.

    Returns:
        Mock: Mock ProcessManager instance with worker process.
    """
    mock_pm = Mock()
    mock_pm.worker_process = Mock()
    return mock_pm


@pytest.fixture
def monitor_with_mocks(mock_socket, mock_process_manager):
    """Create a HeartbeatMonitor with mocked dependencies.

    Sets up a HeartbeatMonitor instance with mocked socket and process
    manager for isolated testing of monitor functionality.

    Args:
        mock_socket: Mock socket fixture.
        mock_process_manager: Mock ProcessManager fixture.

    Returns:
        HeartbeatMonitor: Monitor instance with mocked dependencies.
    """
    monitor = HeartbeatMonitor()
    monitor.heartbeat_socket = mock_socket
    monitor.process_manager = mock_process_manager
    return monitor


def test_initialization_default_values():
    """Test HeartbeatMonitor initialization with default values.

    Verifies that the monitor initializes with correct default configuration
    including timeout threshold, duration, and proper socket setup.
    """
    mock_socket = Mock()
    with patch("src.monitor.socket.socket", return_value=mock_socket):
        monitor = HeartbeatMonitor()

        assert monitor.duration == 60
        assert monitor.timeout_threshold == 500
        assert monitor.last_heartbeat is None
        assert monitor.start_time is None
        assert monitor.heartbeat_socket == mock_socket
        assert monitor.process_manager is None

        mock_socket.bind.assert_called_once_with(("", 9999))
        mock_socket.setblocking.assert_called_once_with(False)


@pytest.mark.parametrize("duration", [30, 60, 120, 300])
def test_initialization_custom_duration(duration):
    """Test HeartbeatMonitor initialization with custom duration values.

    Verifies that the monitor correctly accepts and stores custom duration
    values during initialization.

    Args:
        duration: Custom duration value to test.
    """
    mock_socket = Mock()
    with patch("src.monitor.socket.socket", return_value=mock_socket):
        monitor = HeartbeatMonitor(duration=duration)

        assert monitor.duration == duration


def test_receive_heartbeat_success(monitor_with_mocks, mocker):
    """Test successful heartbeat reception and timestamp update.

    Verifies that heartbeat messages are properly received and that
    the last heartbeat timestamp is correctly updated.

    Args:
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    mock_socket = monitor_with_mocks.heartbeat_socket
    mock_socket.recvfrom.return_value = (b"heartbeat", ("127.0.0.1", 5000))
    mock_logger = mocker.patch("src.monitor.logger")

    with patch("src.monitor.datetime") as mock_datetime:
        mock_now = datetime(2025, 7, 5, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        monitor_with_mocks.receive_heartbeat()

        assert monitor_with_mocks.last_heartbeat == mock_now
        mock_socket.recvfrom.assert_called_once_with(1024)
        mock_logger.info.assert_called_once_with(f"Heartbeat received at {mock_now}")


def test_receive_heartbeat_socket_error(monitor_with_mocks):
    """Test heartbeat reception handles socket errors gracefully.

    Verifies that socket errors during heartbeat reception are handled
    without affecting the monitor's state or causing crashes.

    Args:
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    mock_socket = monitor_with_mocks.heartbeat_socket
    mock_socket.recvfrom.side_effect = socket.error("No data available")

    original_heartbeat = monitor_with_mocks.last_heartbeat

    monitor_with_mocks.receive_heartbeat()

    # Should not change last_heartbeat on socket error
    assert monitor_with_mocks.last_heartbeat == original_heartbeat
    mock_socket.recvfrom.assert_called_once_with(1024)


def test_check_timeout_no_heartbeat_received(monitor_with_mocks):
    """Test timeout check when no heartbeat has been received.

    Verifies that the timeout check correctly handles the case where
    no heartbeat has been received yet.

    Args:
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    monitor_with_mocks.last_heartbeat = None

    result = monitor_with_mocks.check_timeout()

    assert result is False


def test_check_timeout_within_threshold(monitor_with_mocks):
    """Test timeout check when heartbeat is within threshold.

    Verifies that recent heartbeats are correctly identified as within
    the acceptable timeout threshold.

    Args:
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    # Set heartbeat to current time (well within threshold)
    monitor_with_mocks.last_heartbeat = datetime.now()

    result = monitor_with_mocks.check_timeout()

    assert result is False


def test_check_timeout_exceeds_threshold(monitor_with_mocks):
    """Test timeout check when heartbeat exceeds threshold.

    Verifies that old heartbeats are correctly identified as exceeding
    the timeout threshold and requiring process restart.

    Args:
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    # Set heartbeat to 1 second ago (exceeds 500ms threshold)
    monitor_with_mocks.last_heartbeat = datetime.now() - timedelta(seconds=1)

    result = monitor_with_mocks.check_timeout()

    assert result is True


@pytest.mark.parametrize(
    "seconds_ago,expected_timeout",
    [
        (0.1, False),  # 100ms - within threshold
        (0.4, False),  # 400ms - within threshold
        (0.499, False),  # 499ms - within threshold
        (0.6, True),  # 600ms - exceeds threshold
        (1.0, True),  # 1000ms - well over threshold
    ],
)
def test_check_timeout_various_delays(
    monitor_with_mocks, seconds_ago, expected_timeout
):
    """Tests timeout check with various delay scenarios.

    Args:
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
        seconds_ago: How many seconds ago the heartbeat was received.
        expected_timeout: Whether timeout should be detected.
    """
    monitor_with_mocks.last_heartbeat = datetime.now() - timedelta(seconds=seconds_ago)

    result = monitor_with_mocks.check_timeout()

    assert result == expected_timeout


def test_restart_process(monitor_with_mocks, mocker):
    """Tests process restart functionality.

    Args:
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    mock_pm = monitor_with_mocks.process_manager
    mock_logger = mocker.patch("src.monitor.logger")

    with patch("src.monitor.datetime") as mock_datetime:
        mock_now = datetime(2025, 7, 5, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        monitor_with_mocks.restart_process()

        mock_pm.restart_process.assert_called_once()
        assert monitor_with_mocks.last_heartbeat == mock_now
        mock_logger.info.assert_called_once_with(
            "Process restarted and heartbeat tracking reset."
        )


def test_restart_process_no_process_manager(mocker):
    """Test restart_process when process_manager is None.

    Verifies that the restart_process method handles the case where
    process_manager is None by printing an error message without crashing.
    """
    mock_socket = Mock()
    mock_logger = mocker.patch("src.monitor.logger")
    with patch("src.monitor.socket.socket", return_value=mock_socket):
        monitor = HeartbeatMonitor()
        monitor.process_manager = None  # Explicitly set to None

        monitor.restart_process()

        # Should print error message
        mock_logger.error.assert_called_once_with(
            "Error: ProcessManager not available for restart."
        )


@patch("src.monitor.time.sleep")
@patch("src.monitor.time.time")
def test_start_monitoring_duration_reached(
    mock_time, mock_sleep, monitor_with_mocks, mocker
):
    """Tests start_monitoring when duration is reached.

    Args:
        mock_time: Mock time.time function.
        mock_sleep: Mock time.sleep function.
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    mock_pm = monitor_with_mocks.process_manager
    cmd = ["python", "test.py"]
    mock_logger = mocker.patch("src.monitor.logger")

    # Mock time progression: start=0, first check=0, second check=65 (exceeds duration=60)
    mock_time.side_effect = [0, 0, 65]

    with patch("src.monitor.datetime") as mock_datetime:
        mock_now = datetime(2025, 7, 5, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        with patch.object(monitor_with_mocks, "receive_heartbeat"), patch.object(
            monitor_with_mocks, "check_timeout", return_value=False
        ):
            monitor_with_mocks.start_monitoring(cmd)

    mock_pm.start_process.assert_called_once_with(cmd)
    mock_pm.shutdown_system.assert_called_once()
    assert monitor_with_mocks.last_heartbeat == mock_now
    assert monitor_with_mocks.start_time == 0
    mock_logger.info.assert_called_with("Monitoring duration reached. Shutting down.")


@patch("src.monitor.time.sleep")
@patch("src.monitor.time.time")
def test_start_monitoring_with_timeout(
    mock_time, mock_sleep, monitor_with_mocks, mocker
):
    """Tests start_monitoring when timeout is detected.

    Args:
        mock_time: Mock time.time function.
        mock_sleep: Mock time.sleep function.
        monitor_with_mocks: HeartbeatMonitor with mocked dependencies.
    """
    mock_pm = monitor_with_mocks.process_manager
    cmd = ["python", "test.py"]
    mocker.patch("src.monitor.logger")

    # Mock time to stay within duration
    mock_time.side_effect = [0, 0, 30, 65]  # Last value triggers duration exit

    with patch("src.monitor.datetime") as mock_datetime:
        mock_now = datetime(2025, 7, 5, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        with patch.object(monitor_with_mocks, "receive_heartbeat"), patch.object(
            monitor_with_mocks, "check_timeout", side_effect=[True, False]
        ), patch.object(monitor_with_mocks, "restart_process") as mock_restart:
            monitor_with_mocks.start_monitoring(cmd)

    mock_pm.start_process.assert_called_once_with(cmd)
    mock_restart.assert_called_once()
    mock_pm.shutdown_system.assert_called_once()


def test_start_monitoring_skips_terminate_when_no_worker(monkeypatch, mock_socket):
    """
    Tests that start_monitoring does not call terminate_process when no worker_process exists.
    """
    from unittest.mock import Mock

    from src.monitor import HeartbeatMonitor

    # Setup mock process manager with no worker_process
    mock_pm = Mock()
    mock_pm.worker_process = None

    # Patch socket.socket to use our mock
    monkeypatch.setattr(
        "src.monitor.socket.socket", lambda *args, **kwargs: mock_socket
    )

    # Simulate time advancing past duration immediately
    times = iter([0, 2])
    monkeypatch.setattr("src.monitor.time.time", lambda: next(times))

    monitor = HeartbeatMonitor(duration=1)
    monitor.heartbeat_socket = mock_socket
    monitor.process_manager = mock_pm

    monitor.start_monitoring(["cmd"])

    # shutdown_system should be called to handle cleanup
    mock_pm.shutdown_system.assert_called_once()


def test_start_monitoring_no_process_manager():
    """Test that start_monitoring raises ValueError when process_manager is None.

    Verifies that the monitor properly validates that a ProcessManager is set
    before attempting to start monitoring operations.
    """
    mock_socket = Mock()
    with patch("src.monitor.socket.socket", return_value=mock_socket):
        monitor = HeartbeatMonitor()
        # process_manager is None by default

        cmd = ["python", "src/detector.py"]

        with pytest.raises(
            ValueError,
            match="ProcessManager not set. Must be configured by orchestrator.",
        ):
            monitor.start_monitoring(cmd)


class TestHeartbeatMonitorIntegration:
    """Integration tests for HeartbeatMonitor workflow scenarios."""

    @pytest.fixture
    def monitor(self):
        """Creates a HeartbeatMonitor for integration tests."""
        mock_socket = Mock()
        with patch("src.monitor.socket.socket", return_value=mock_socket):
            return HeartbeatMonitor()

    def test_heartbeat_reception_workflow(self, monitor, mocker):
        """Tests the complete heartbeat reception workflow.

        Args:
            monitor: HeartbeatMonitor fixture.
        """
        # Test initial state
        assert monitor.last_heartbeat is None
        assert monitor.check_timeout() is False
        mock_logger = mocker.patch("src.monitor.logger")

        # Simulate receiving heartbeat
        monitor.heartbeat_socket.recvfrom.return_value = (
            b"heartbeat",
            ("127.0.0.1", 5000),
        )

        with patch("src.monitor.datetime") as mock_datetime:
            mock_now = datetime(2025, 7, 5, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            monitor.receive_heartbeat()

            # Verify heartbeat was processed
            assert monitor.last_heartbeat == mock_now
            assert monitor.check_timeout() is False
            mock_logger.info.assert_called_once_with(
                f"Heartbeat received at {mock_now}"
            )

    def test_timeout_detection_workflow(self, monitor, mocker):
        """Tests timeout detection and recovery workflow.

        Args:
            monitor: HeartbeatMonitor fixture.
        """
        # Set up old heartbeat
        old_time = datetime.now() - timedelta(seconds=1)
        monitor.last_heartbeat = old_time
        mock_logger = mocker.patch("src.monitor.logger")

        # Should detect timeout
        assert monitor.check_timeout() is True

        # Set up process manager
        mock_pm = Mock()
        monitor.process_manager = mock_pm

        # Simulate restart process
        with patch("src.monitor.datetime") as mock_datetime:
            new_time = datetime.now()
            mock_datetime.now.return_value = new_time

            monitor.restart_process()

            # Should reset heartbeat and clear timeout
            assert monitor.last_heartbeat == new_time
            assert monitor.check_timeout() is False
            mock_pm.restart_process.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "Process restarted and heartbeat tracking reset."
            )

    def test_socket_error_handling(self, monitor):
        """Tests robust error handling for socket operations.

        Args:
            monitor: HeartbeatMonitor fixture.
        """
        # Test various socket errors
        error_types = [
            socket.error("Connection refused"),
            socket.timeout("Socket timeout"),
            OSError("Network unreachable"),
        ]

        for error in error_types:
            monitor.heartbeat_socket.recvfrom.side_effect = error
            original_heartbeat = monitor.last_heartbeat

            # Should not raise exception
            monitor.receive_heartbeat()

            # Should not change heartbeat state
            assert monitor.last_heartbeat == original_heartbeat

    def test_configuration_validation(self, monitor):
        """Tests that monitor configuration is properly validated.

        Args:
            monitor: HeartbeatMonitor fixture.
        """
        # Test default configuration
        assert monitor.duration == 60
        assert monitor.timeout_threshold == 500
        assert monitor.last_heartbeat is None
        assert monitor.start_time is None

        # Test socket configuration
        assert monitor.heartbeat_socket is not None
        assert monitor.process_manager is None

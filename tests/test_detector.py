"""Test suite for the ObstacleDetector class.

This module contains comprehensive unit tests for the obstacle detection system,
including heartbeat functionality, detection loop behavior, failure simulation,
and configuration validation.
"""

import socket
from datetime import datetime

import pytest

from src.detector import ObstacleDetector


@pytest.fixture
def detector():
    """Create an ObstacleDetector instance for testing.

    Returns:
        ObstacleDetector: Configured detector instance with default settings.
    """
    return ObstacleDetector()


@pytest.fixture
def mocked_detector(mocker):
    """Create an ObstacleDetector instance with mocked socket for testing.

    Args:
        mocker: Pytest mocker fixture for creating mock objects.

    Returns:
        ObstacleDetector: Configured detector instance with mocked socket.
    """
    detector = ObstacleDetector()
    detector.heartbeat_socket = mocker.Mock(spec=socket.socket)
    return detector


def test_send_heartbeat(mocked_detector, mocker):
    """Verify heartbeat message formatting and transmission.

    Tests that heartbeat messages are properly formatted with timestamps
    and sent to the correct monitor address via UDP socket.

    Args:
        mocked_detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_datetime = mocker.patch("src.detector.datetime")
    mock_now = datetime(2025, 7, 5, 12, 0, 0)
    mock_datetime.now.return_value = mock_now

    mock_logger = mocker.patch("src.detector.logger")

    mocked_detector.send_heartbeat()

    expected_message = mock_now.strftime("%Y-%m-%d %H:%M:%S.%f").encode("utf-8")
    mocked_detector.heartbeat_socket.sendto.assert_called_once_with(
        expected_message, ("localhost", 9999)
    )
    mock_logger.info.assert_called_once_with(f"Heartbeat sent at {mock_now}")


def test_run_detection_loop(mocked_detector, mocker):
    """Validate detection loop execution for specified iterations.

    Tests that the detection loop runs for the exact number of specified
    iterations, sending heartbeats and performing detection activities.

    Args:
        mocked_detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_sleep = mocker.patch("src.detector.time.sleep")
    mocker.patch("src.detector.random.uniform", return_value=42.0)
    mocker.patch(
        "src.detector.random.random", return_value=0.5
    )  # Prevent failure simulation

    mocked_detector.run_detection_loop(max_iterations=3)

    assert (
        mocked_detector.heartbeat_socket.sendto.call_count == 3
    ), "Should send 3 heartbeats"
    # Verify sleep was called for main loop intervals
    assert mock_sleep.call_count >= 3, "Should sleep at least 3 times for main loop"


def test_detect_obstacles(detector, mocker):
    """Test obstacle detection simulation with timing and distance calculation.

    Verifies that obstacle detection includes proper timing delays and
    generates random distance measurements as expected.

    Args:
        detector: ObstacleDetector fixture.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_sleep = mocker.patch("src.detector.time.sleep")
    mock_random = mocker.patch("src.detector.random.uniform", return_value=42.0)

    mock_logger = mocker.patch("src.detector.logger")

    detector.detect_obstacles()

    mock_sleep.assert_called_once()
    assert mock_random.call_count == 2  # Sleep duration and distance calculation
    mock_logger.info.assert_called_once_with("Detected obstacle at 42.00 meters.")


@pytest.mark.parametrize(
    "random_value,should_exit",
    [
        (0.5, False),  # Above threshold, no exit
        (0.02, False),  # Just above threshold, no exit
        (0.009, True),  # Below threshold, should exit
        (0.005, True),  # Well below threshold, should exit
    ],
)
def test_simulate_failure(detector, mocker, random_value, should_exit):
    """Test failure simulation with various probability values.

    Verifies that the failure simulation correctly triggers or avoids
    process termination based on random probability thresholds.

    Args:
        detector: ObstacleDetector fixture.
        mocker: Pytest mocker fixture for patching dependencies.
        random_value: Mocked random value to test.
        should_exit: Whether the test should expect a SystemExit.
    """
    mock_random = mocker.patch("src.detector.random.random", return_value=random_value)

    mock_exit = mocker.patch("builtins.exit")

    detector.simulate_failure()

    mock_random.assert_called_once()
    if should_exit:
        mock_exit.assert_called_once_with(1)
    else:
        mock_exit.assert_not_called()


@pytest.mark.parametrize(
    "attribute,expected_value,description",
    [
        ("heartbeat_interval", 50, "Heartbeat interval should be 50 milliseconds"),
        (
            "monitor_address",
            ("localhost", 9999),
            "Monitor address should be localhost:9999",
        ),
    ],
)
def test_configuration_values(detector, attribute, expected_value, description):
    """Validate default configuration values.

    Tests that the detector initializes with correct default values
    for all critical configuration parameters.

    Args:
        detector: ObstacleDetector fixture.
        attribute: The attribute name to test.
        expected_value: The expected value for the attribute.
        description: Description for the assertion.
    """
    assert getattr(detector, attribute) == expected_value, description


@pytest.fixture
def real_socket():
    """Create a real socket for testing and ensure cleanup.

    Provides a real UDP socket for integration testing and automatically
    handles cleanup to prevent resource leaks.

    Yields:
        socket.socket: A real UDP socket for testing.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        yield sock
    finally:
        sock.close()


def test_heartbeat_socket_configuration(real_socket):
    """Confirm socket is configured for IPv4 UDP communication.

    Validates that the heartbeat socket is properly configured for
    IPv4 UDP communication as required by the heartbeat protocol.

    Args:
        real_socket: Real socket fixture with automatic cleanup.
    """
    assert real_socket.family == socket.AF_INET, "Heartbeat socket should use IPv4"
    assert real_socket.type == socket.SOCK_DGRAM, "Heartbeat socket should be UDP"


def test_stop_detection_loop(mocked_detector, mocker):
    """Test graceful termination of the detection loop.

    Verifies that the detection loop can be stopped gracefully and
    that the running state is properly updated.

    Args:
        mocked_detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_sleep = mocker.patch("src.detector.time.sleep")
    mocker.patch("src.detector.random.uniform", return_value=42.0)
    mocker.patch(
        "src.detector.random.random", return_value=0.5
    )  # Prevent failure simulation

    def stop_after_first_sleep(*args, **kwargs):
        mocked_detector.stop()

    mock_sleep.side_effect = stop_after_first_sleep

    mocked_detector.run_detection_loop()

    assert not mocked_detector._running, "Loop should be stopped"
    assert (
        mocked_detector.heartbeat_socket.sendto.call_count == 1
    ), "Should send one heartbeat before stopping"


def test_detector_initialization():
    """Test that detector initializes with correct default state.

    Verifies that a new detector instance is created with all expected
    default values and proper socket configuration.
    """
    detector = ObstacleDetector()

    assert detector.heartbeat_interval == 50
    assert detector.monitor_address == ("localhost", 9999)
    assert detector._running is False
    assert detector.heartbeat_socket is not None

    # Clean up
    detector.heartbeat_socket.close()


def test_stop_method():
    """Test the stop method sets the running flag to False.

    Verifies that the stop method correctly updates the internal running
    state to allow graceful termination of the detection loop.
    """
    detector = ObstacleDetector()

    detector._running = True
    detector.stop()

    assert detector._running is False

    # Clean up
    detector.heartbeat_socket.close()

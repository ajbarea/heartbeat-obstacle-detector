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
    """Creates an ObstacleDetector instance for testing.

    Returns:
        ObstacleDetector: Configured detector instance.
    """
    return ObstacleDetector()


@pytest.fixture
def mocked_detector(mocker):
    """Creates an ObstacleDetector instance with mocked socket for testing.

    Args:
        mocker: Pytest mocker fixture for creating mock objects.

    Returns:
        ObstacleDetector: Configured detector instance with mocked socket.
    """
    detector = ObstacleDetector()
    detector.heartbeat_socket = mocker.Mock(spec=socket.socket)
    return detector


def test_send_heartbeat(mocked_detector, mocker):
    """Verifies heartbeat message formatting and transmission.

    Args:
        mocked_detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_datetime = mocker.patch("src.detector.datetime")
    mock_now = datetime(2025, 7, 5, 12, 0, 0)
    mock_datetime.now.return_value = mock_now

    mocked_detector.send_heartbeat()

    expected_message = mock_now.strftime("%Y-%m-%d %H:%M:%S.%f").encode("utf-8")
    mocked_detector.heartbeat_socket.sendto.assert_called_once_with(
        expected_message, ("localhost", 9999)
    )


def test_run_detection_loop(mocked_detector, mocker):
    """Validates detection loop execution for specified iterations.

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
    """Tests obstacle detection simulation with timing and distance calculation.

    Args:
        detector: ObstacleDetector fixture.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_sleep = mocker.patch("src.detector.time.sleep")
    mock_random = mocker.patch("src.detector.random.uniform", return_value=42.0)

    detector.detect_obstacles()

    mock_sleep.assert_called_once()
    assert mock_random.call_count == 2  # Sleep duration and distance calculation


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
    """Tests failure simulation with various probability values.

    Args:
        detector: ObstacleDetector fixture.
        mocker: Pytest mocker fixture for patching dependencies.
        random_value: Mocked random value to test.
        should_exit: Whether the test should expect a SystemExit.
    """
    mock_random = mocker.patch("src.detector.random.random", return_value=random_value)

    if should_exit:
        with pytest.raises(SystemExit):
            detector.simulate_failure()
    else:
        detector.simulate_failure()  # Should not raise

    mock_random.assert_called_once()


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
    """Validates default configuration values.

    Args:
        detector: ObstacleDetector fixture.
        attribute: The attribute name to test.
        expected_value: The expected value for the attribute.
        description: Description for the assertion.
    """
    assert getattr(detector, attribute) == expected_value, description


@pytest.fixture
def real_socket():
    """Creates a real socket for testing and ensures cleanup.

    Yields:
        socket.socket: A real UDP socket for testing.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        yield sock
    finally:
        sock.close()


def test_heartbeat_socket_configuration(real_socket):
    """Confirms socket is configured for IPv4 UDP communication.

    Args:
        real_socket: Real socket fixture with automatic cleanup.
    """
    assert real_socket.family == socket.AF_INET, "Heartbeat socket should use IPv4"
    assert real_socket.type == socket.SOCK_DGRAM, "Heartbeat socket should be UDP"


def test_stop_detection_loop(mocked_detector, mocker):
    """Tests graceful termination of the detection loop.

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
    """Tests that detector initializes with correct default state."""
    detector = ObstacleDetector()

    assert detector.heartbeat_interval == 50
    assert detector.monitor_address == ("localhost", 9999)
    assert detector._running is False
    assert detector.heartbeat_socket is not None

    # Clean up
    detector.heartbeat_socket.close()


def test_stop_method():
    """Tests the stop method sets the running flag to False."""
    detector = ObstacleDetector()

    detector._running = True
    detector.stop()

    assert detector._running is False

    # Clean up
    detector.heartbeat_socket.close()

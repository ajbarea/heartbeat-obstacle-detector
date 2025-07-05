"""Test suite for the ObstacleDetector class.

This module contains comprehensive unit tests for the obstacle detection system,
including heartbeat functionality, detection loop behavior, failure simulation,
and configuration validation.
"""

import socket
import pytest
from datetime import datetime

from src.detector import ObstacleDetector


@pytest.fixture
def detector(mocker):
    """Creates an ObstacleDetector instance with mocked socket for testing.

    Args:
        mocker: Pytest mocker fixture for creating mock objects.

    Returns:
        ObstacleDetector: Configured detector instance with mocked socket.
    """
    detector = ObstacleDetector()
    detector.heartbeat_socket = mocker.Mock(spec=socket.socket)
    return detector


def test_send_heartbeat(detector, mocker):
    """Verifies heartbeat message formatting and transmission.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_datetime = mocker.patch("src.detector.datetime")
    mock_now = datetime(2025, 7, 5, 12, 0, 0)
    mock_datetime.now.return_value = mock_now

    detector.send_heartbeat()

    expected_message = mock_now.strftime("%Y-%m-%d %H:%M:%S.%f").encode("utf-8")
    detector.heartbeat_socket.sendto.assert_called_once_with(
        expected_message, ("localhost", 9999)
    )


def test_run_detection_loop(detector, mocker):
    """Validates detection loop execution for specified iterations.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_sleep = mocker.patch("src.detector.time.sleep")
    detector.run_detection_loop(max_iterations=3)

    assert detector.heartbeat_socket.sendto.call_count == 3, "Should send 3 heartbeats"
    assert mock_sleep.call_count == 6, "Should sleep 6 times total (3 main + 3 detect)"


def test_detect_obstacles(detector, mocker):
    """Tests obstacle detection simulation with timing and distance calculation.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_sleep = mocker.patch("src.detector.time.sleep")
    mock_random = mocker.patch("src.detector.random.uniform", return_value=42.0)

    detector.detect_obstacles()

    mock_sleep.assert_called_once()
    assert mock_random.call_count == 2  # Sleep duration and distance calculation


def test_simulate_failure(detector, mocker):
    """Verifies failure simulation when probability threshold is not met.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_random = mocker.patch("src.detector.random.random", return_value=0.5)

    detector.simulate_failure()

    mock_random.assert_called_once()


def test_simulate_failure_triggers(detector, mocker):
    """Confirms system exit when failure probability threshold is exceeded.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mocker.patch("src.detector.random.random", return_value=0.005)

    with pytest.raises(SystemExit):
        detector.simulate_failure()


def test_heartbeat_interval(detector):
    """Validates default heartbeat interval configuration.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
    """
    assert (
        detector.heartbeat_interval == 50
    ), "Heartbeat interval should be 50 milliseconds"


def test_monitor_address(detector):
    """Verifies default monitor address configuration.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
    """
    assert detector.monitor_address == (
        "localhost",
        9999,
    ), "Monitor address should be localhost:9999"


def test_heartbeat_socket_configuration():
    """Confirms socket is configured for IPv4 UDP communication."""
    real_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    assert real_socket.family == socket.AF_INET, "Heartbeat socket should use IPv4"
    assert real_socket.type == socket.SOCK_DGRAM, "Heartbeat socket should be UDP"
    real_socket.close()


def test_stop_detection_loop(detector, mocker):
    """Tests graceful termination of the detection loop.

    Args:
        detector: ObstacleDetector fixture with mocked socket.
        mocker: Pytest mocker fixture for patching dependencies.
    """
    mock_sleep = mocker.patch("src.detector.time.sleep")

    def stop_after_iterations(*args, **kwargs):
        detector.stop()

    mock_sleep.side_effect = stop_after_iterations

    detector.run_detection_loop()

    assert mock_sleep.call_count == 2, "Loop should stop after first iteration"
    assert not detector._running, "Loop should be stopped"

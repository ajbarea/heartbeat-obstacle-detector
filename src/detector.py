"""Obstacle detection system with heartbeat-based fault monitoring.

This module implements an obstacle detector that sends periodic heartbeats to a monitor
process while simulating obstacle detection. It uses UDP sockets for heartbeat communication
and includes failure simulation for testing fault detection.
"""

import random
import socket
import time
from datetime import datetime
from typing import Optional

from config import HEARTBEAT_HOST, HEARTBEAT_INTERVAL, HEARTBEAT_PORT
from logger import get_logger

logger = get_logger(__name__)


class ObstacleDetector:
    """Simulates an obstacle detection system with heartbeat monitoring.

    This class implements a fault-tolerant obstacle detector that periodically sends
    heartbeat signals to a monitoring process while performing simulated obstacle
    detection. It includes controlled failure simulation for testing purposes.

    Attributes:
        _heartbeat_interval (int): Interval between heartbeats in milliseconds.
        _heartbeat_socket (socket.socket): UDP socket for sending heartbeat messages.
        _monitor_address (tuple): Tuple of (host, port) for the monitoring process.
    """

    def __init__(self) -> None:
        """Initializes the obstacle detector with default configuration.

        The detector is configured with a 50ms heartbeat interval and establishes
        a UDP socket connection to the monitor process on localhost:9999.
        """
        self._heartbeat_interval = HEARTBEAT_INTERVAL  # milliseconds
        self._heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._monitor_address = (HEARTBEAT_HOST, HEARTBEAT_PORT)
        self._running = False

    def run_detection_loop(self, max_iterations: Optional[int] = None) -> None:
        """Runs the main detection loop.

        Executes the core functionality in a continuous loop:
        1. Sends heartbeat signals
        2. Performs obstacle detection
        3. Simulates potential failures
        4. Maintains the specified heartbeat interval

        Args:
            max_iterations (int, optional): Maximum number of loop iterations.
                If None, runs indefinitely. Defaults to None.
        """
        self._running = True
        iteration = 0

        while self._running:
            if max_iterations is not None:
                if iteration >= max_iterations:
                    break
                iteration += 1

            self.send_heartbeat()
            self.detect_obstacles()
            self.simulate_failure()
            time.sleep(self._heartbeat_interval / 1000)

    def stop(self) -> None:
        """Stops the detection loop gracefully."""
        self._running = False

    def send_heartbeat(self) -> None:
        """Sends a timestamped heartbeat message to the monitor process.

        Creates and transmits a heartbeat message containing the current timestamp
        via UDP to the configured monitor address.
        """
        now = datetime.now()
        message = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        self._heartbeat_socket.sendto(message.encode("utf-8"), self._monitor_address)
        logger.info(f"Heartbeat sent at {now}")

    def simulate_failure(self) -> None:
        """Simulates random process failures for testing.

        Introduces a 1% chance of process termination on each call,
        simulating unexpected crashes for fault tolerance testing.
        """
        if random.random() < 0.01:
            logger.warning("Simulating a crash...")
            exit(1)

    def detect_obstacles(self) -> None:
        """Simulates obstacle detection with random delays and distances.

        Mimics a real obstacle detection process by introducing random processing
        delays and generating random distance measurements.
        """
        time.sleep(random.uniform(0.01, 0.03))
        distance = random.uniform(1, 100)
        logger.info(f"Detected obstacle at {distance:.2f} meters.")


def main() -> None:  # pragma: no cover
    """Main entry point for standalone detector usage.

    Runs the detector independently for testing purposes.
    Use process_manager.py for complete system orchestration.
    """
    logger.info("Starting ObstacleDetector in standalone mode...")
    logger.info(
        "Use 'python src/process_manager.py' for complete system orchestration."
    )

    detector = ObstacleDetector()

    try:
        detector.run_detection_loop()
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal. Stopping detector...")
        detector.stop()
    except Exception as e:
        logger.error(f"Detector error: {e}")
        detector.stop()


if __name__ == "__main__":
    main()

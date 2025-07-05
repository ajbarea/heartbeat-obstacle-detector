# 🚗💓 Heartbeat Obstacle Detector

[![codecov](https://codecov.io/gh/ajbarea/heartbeat-obstacle-detector/graph/badge.svg?token=7HZoKzaPld)](https://codecov.io/gh/ajbarea/heartbeat-obstacle-detector) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ajbarea_heartbeat-obstacle-detector&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=ajbarea_heartbeat-obstacle-detector)

A proof-of-concept implementation of the **Heartbeat** architectural tactic for fault detection and recovery, applied to an obstacle detection module in a self-driving car case study.

---

## 📋 Table of Contents

- [📖 Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [💪 Architecture Strengths](#-architecture-strengths)
- [📡 UDP Communication](#-why-udp-for-heartbeats)
- [🔧 Components](#-components)
- [🚀 Installation](#-installation)
- [💻 Usage](#-usage)
- [📁 Project Structure](#-project-structure)

---

## 📖 Overview

This repository contains three Python modules implementing a fault-tolerant heartbeat monitoring system:

1. **⚙️ process_manager.py**: **Main orchestrator** that coordinates the entire system and manages component lifecycle.
2. **👁️ monitor.py**: **Monitoring service** that listens for heartbeat messages and detects timeouts.
3. **🔍 detector.py**: **Worker process** that simulates obstacle detection and sends periodic heartbeat messages.

The purpose is to demonstrate how the Heartbeat tactic can detect faults and recover a critical sensing process in a distributed system with proper architectural separation.

---

## 🏗️ Architecture

The system uses a **hierarchical orchestration pattern** with clear separation of concerns:

- **⚙️ ProcessManager (Main Orchestrator)**: Coordinates the entire system, manages component lifecycle, and serves as the primary entry point.
- **👁️ HeartbeatMonitor (Monitoring Service)**: Focuses on UDP heartbeat detection, timeout monitoring, and fault notification.
- **🔍 ObstacleDetector (Worker Process)**: Performs obstacle detection simulation and sends periodic heartbeat signals.

**Key Architectural Improvements:**

- **Single Entry Point**: ProcessManager serves as the main orchestrator
- **Service-Oriented Design**: HeartbeatMonitor operates as a focused service
- **Centralized Control**: All system lifecycle management in one place
- **Proper Dependencies**: Clear hierarchy prevents circular dependencies

For detailed architecture diagrams and technical documentation, see **[📋 Software Architecture Documentation](docs/software_architecture.md)**.

---

## 💪 Architecture Strengths

This heartbeat-based fault detection system provides several key advantages:

**🔄 Automatic Recovery**: Detects process failures within 500ms and automatically restarts the obstacle detection module without manual intervention.

**🏗️ Modular Design**: Clean separation between monitoring, process management, and detection logic enables independent testing and maintenance.

**📡 Lightweight Communication**: UDP-based heartbeats minimize network overhead while providing timely fault detection.

**🛡️ Fault Isolation**: Process crashes are contained and don't affect the monitoring system, ensuring continuous supervision.

**⚡ Real-time Response**: 50ms heartbeat interval provides rapid fault detection suitable for safety-critical automotive applications.

---

## 📡 Why UDP for Heartbeats

In our self-driving car POC, UDP’s connectionless “fire-and-forget” design lets the obstacle detector send sub-millisecond heartbeats without TCP style handshakes, retransmits, or blocking.

**🚀 Ultra-Low Latency:** No connection setup or retransmit delays.

**📉 Minimal Overhead:** Lightweight datagrams cut bandwidth and CPU use.

**🔁 Stateless, Fire-and-Forget:** Missed packets merely indicate a failure—no blocking or retries.

**🌡️ Fault-Tolerant by Design:** Occasional loss is acceptable; the next heartbeat arrives almost immediately.

**⚙️ Simple Implementation:** Plain UDP sockets—no connection management or session state.

---

## 🔧 Components

- 🔍 `detector.py`
- 👁️ `monitor.py`
- ⚙️ `process_manager.py`
- 📦 `pyproject.toml`
- `README.md`
- 📁 `docs/` (Mermaid diagrams and documentation)
- 📁 `tests/` (Test files)

---

## 🚀 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ajbarea/heartbeat-obstacle-detector.git
   cd heartbeat-obstacle-detector
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Bash
   python -m pip install --upgrade pip
   pip install -e ".[dev]"
   ```

## 💻 Usage

### Usage Options

1. **Start the complete system** (recommended):

    ```bash
    python src/process_manager.py

    # With custom duration (e.g., 120 seconds)
    python src/process_manager.py 120
    ```

2. **Monitor service** (standalone mode):

    ```bash
    python src/monitor.py
    ```

3. **Detector worker** (standalone mode):

    ```bash
    python src/detector.py
    ```

### System Operation

- The ProcessManager orchestrates the entire system lifecycle
- HeartbeatMonitor automatically detects timeouts and coordinates restarts
- ObstacleDetector sends heartbeats every 50ms with 1% random failure rate
- System runs for specified duration (default 60 seconds) then gracefully shuts down

## 📁 Project Structure

```text
heartbeat-obstacle-detector/
├── src/
│   ├── process_manager.py          # Main orchestrator and system entry point
│   ├── monitor.py                  # Heartbeat monitoring service
│   └── detector.py                 # Obstacle detector worker process
├── tests/
│   ├── test_detector.py           # Unit tests for detector
│   ├── test_monitor.py            # Unit tests for monitor
│   └── test_process_manager.py    # Unit tests for process manager
├── docs/
│   ├── class.mermaid              # Class diagram source
│   ├── sequence.mermaid           # Sequence diagram source
│   └── software_architecture.md   # Detailed architecture docs
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI workflow
├── pyproject.toml                 # Project configuration and dependencies
├── README.md                      # This file
├── lint.sh                        # Linting script for pre-commit hooks
```

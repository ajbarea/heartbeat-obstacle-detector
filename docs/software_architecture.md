# Software Architecture

## 📋 Table of Contents

- [Class Diagram](#class-diagram)
- [Sequence Diagram](#sequence-diagram)

<!-- ## Theme Configuration

For consistency across all diagrams, use this configuration block at the start of each Mermaid diagram:

```javascript
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#E8F4FD",
    "primaryBorderColor": "#2196F3",
    "primaryTextColor": "#1565C0",
    "secondaryColor": "#F3E5F5",
    "secondaryBorderColor": "#9C27B0",
    "secondaryTextColor": "#6A1B9A",
    "tertiaryColor": "#E8F5E8",
    "tertiaryBorderColor": "#4CAF50",
    "tertiaryTextColor": "#2E7D32",
    "lineColor": "#424242",
    "background": "#FAFAFA",
    "textColor": "#212121",
    "nodeTextColor": "#1565C0",
    "edgeLabelBackground": "#FFFFFF",
    "clusterBkg": "#F5F5F5",
    "clusterBorder": "#BDBDBD",
    "fillType0": "#E3F2FD",
    "fillType1": "#F3E5F5",
    "fillType2": "#E8F5E8",
    "fillType3": "#FFF3E0",
    "fillType4": "#FCE4EC",
    "fillType5": "#F1F8E9",
    "fillType6": "#E0F2F1",
    "fillType7": "#FFF8E1"
  }
}}%%
``` -->

## Class Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#E8F4FD", "primaryBorderColor": "#2196F3", "primaryTextColor": "#1565C0", "secondaryColor": "#F3E5F5", "secondaryBorderColor": "#9C27B0", "secondaryTextColor": "#6A1B9A", "tertiaryColor": "#E8F5E8", "tertiaryBorderColor": "#4CAF50", "tertiaryTextColor": "#2E7D32", "lineColor": "#424242", "background": "#FAFAFA", "textColor": "#212121", "nodeTextColor": "#1565C0", "edgeLabelBackground": "#FFFFFF", "clusterBkg": "#F5F5F5", "clusterBorder": "#BDBDBD", "fillType0": "#E3F2FD", "fillType1": "#F3E5F5", "fillType2": "#E8F5E8", "fillType3": "#FFF3E0", "fillType4": "#FCE4EC", "fillType5": "#F1F8E9", "fillType6": "#E0F2F1", "fillType7": "#FFF8E1"}}}%%
classDiagram
    class HeartbeatMonitor {
        - _timeout_threshold: int
        - _last_heartbeat: Optional[datetime]
        - _heartbeat_socket: socket
        - _process_manager: Optional[ProcessManager]
        - _duration: int
        - _start_time: Optional[float]
        + start_monitoring(cmd: List[str]): void
        + receive_heartbeat(): void
        + check_timeout(): bool
        + restart_process(): void
    }

    class ProcessManager {
        - _worker_cmd: Optional[List[str]]
        - _worker_process: Optional[subprocess.Popen]
        - _monitor: Optional[HeartbeatMonitor]
        - _duration: int
        + start_process(cmd: List[str]): subprocess.Popen
        + restart_process(): subprocess.Popen
        + terminate_process(proc: subprocess.Popen): void
        + is_process_running(): bool
        + start_system(detector_cmd: List[str]): void
        + shutdown_system(): void
    }

    class ObstacleDetector {
        - _heartbeat_interval: int
        - _heartbeat_socket: socket
        - _monitor_address: tuple
        - _running: bool
        + run_detection_loop(max_iterations: Optional[int]): void
        + send_heartbeat(): void
        + simulate_failure(): void
        + detect_obstacles(): void
        + stop(): void
    }

    ProcessManager --> HeartbeatMonitor : orchestrates
    ProcessManager ..> ObstacleDetector : manages subprocess
    ObstacleDetector ..> HeartbeatMonitor : UDP heartbeat
    HeartbeatMonitor ..> ProcessManager : notifies

```

## Sequence Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#E8F4FD", "primaryBorderColor": "#2196F3", "primaryTextColor": "#1565C0", "secondaryColor": "#F3E5F5", "secondaryBorderColor": "#9C27B0", "secondaryTextColor": "#6A1B9A", "tertiaryColor": "#E8F5E8", "tertiaryBorderColor": "#4CAF50", "tertiaryTextColor": "#2E7D32", "lineColor": "#424242", "background": "#FAFAFA", "textColor": "#212121", "nodeTextColor": "#1565C0", "edgeLabelBackground": "#FFFFFF", "clusterBkg": "#F5F5F5", "clusterBorder": "#BDBDBD", "fillType0": "#E3F2FD", "fillType1": "#F3E5F5", "fillType2": "#E8F5E8", "fillType3": "#FFF3E0", "fillType4": "#FCE4EC", "fillType5": "#F1F8E9", "fillType6": "#E0F2F1", "fillType7": "#FFF8E1"}}}%%
sequenceDiagram
    participant P as ProcessManager
    participant M as HeartbeatMonitor
    participant W as ObstacleDetector

    Note over P,M: System Initialization
    activate P
    P->>M: create HeartbeatMonitor()
    activate M
    M-->>P: monitor service ready
    P->>M: set process_manager reference
    P->>M: start_monitoring(["python", "detector.py"])
    M->>P: start_process(["python", "detector.py"])
    P->>W: launch subprocess
    activate W
    W-->>P: process started
    P-->>M: detector launched
    deactivate P

    loop Every 50 ms
        W-->>M: send_heartbeat()
        Note right of M: Record timestamp
    end

    alt Detector crash
        Note right of W: Simulated crash (1% chance)<br>No more heartbeats
    end

    alt Timeout > 500 ms
        M->>M: check_timeout()
        Note right of M: Timeout detected
        M->>P: restart_process()
        activate P
        P->>W: terminate old process
        P->>W: launch new process
        activate W
        W-->>P: process started
        P-->>M: restarted successfully
        deactivate P
        Note right of M: Heartbeat tracking reset
    end

    alt System Shutdown
        activate P
        P->>P: shutdown_system()
        P->>W: terminate process
        P->>M: close socket
        Note right of P: System shutdown complete
        deactivate M
        deactivate P
    end
```

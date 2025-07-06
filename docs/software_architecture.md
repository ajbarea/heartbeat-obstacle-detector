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
    ProcessManager --> ObstacleDetector : manages
    ObstacleDetector --> HeartbeatMonitor : sendHeartbeat
    HeartbeatMonitor ..> ProcessManager : notifies

```

## Sequence Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#E8F4FD", "primaryBorderColor": "#2196F3", "primaryTextColor": "#1565C0", "secondaryColor": "#F3E5F5", "secondaryBorderColor": "#9C27B0", "secondaryTextColor": "#6A1B9A", "tertiaryColor": "#E8F5E8", "tertiaryBorderColor": "#4CAF50", "tertiaryTextColor": "#2E7D32", "lineColor": "#424242", "background": "#FAFAFA", "textColor": "#212121", "nodeTextColor": "#1565C0", "edgeLabelBackground": "#FFFFFF", "clusterBkg": "#F5F5F5", "clusterBorder": "#BDBDBD", "fillType0": "#E3F2FD", "fillType1": "#F3E5F5", "fillType2": "#E8F5E8", "fillType3": "#FFF3E0", "fillType4": "#FCE4EC", "fillType5": "#F1F8E9", "fillType6": "#E0F2F1", "fillType7": "#FFF8E1"}}}%%
sequenceDiagram
    participant M as HeartbeatMonitor
    participant P as ProcessManager
    participant W as ObstacleDetector

    Note over M,P: Initialization
    activate M
    M->>P: start_process("detector.py")
    activate P
    P->>W: launch
    activate W
    W-->>P: acknowledgment
    deactivate W
    P-->>M: started successfully
    deactivate P
    deactivate M

    loop Every 50 ms
        activate W
        W->>M: send_heartbeat()
        deactivate W
        Note right of M: record timestamp locally
    end

    alt Crash
        activate W
        W->>W: simulate_failure()
        deactivate W
        Note right of W: no more heartbeats
    end

    alt Timeout (> 500 ms)
        activate M
        M->>M: check_timeout()
        Note right of M: timeout detected
        M->>P: restart_process("detector.py")
        activate P
        P->>W: launch
        activate W
        W-->>P: acknowledgment
        deactivate W
        P-->>M: restarted successfully
        deactivate P
        deactivate M
    end
```

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
        - timeout_threshold: int
        - last_heartbeat: datetime
        - heartbeat_socket: socket
        + start_monitoring(cmd: str): void
        + receive_heartbeat(): void
        + check_timeout(): bool
        + restart_process(cmd: str): void
    }

    class ProcessManager {
        - worker_cmd: str
        - worker_process: Process
        + start_process(cmd: str): Process
        + restart_process(cmd: str): Process
        + terminate_process(proc: Process): void
        + is_process_running(): bool
    }

    class ObstacleDetector {
        - heartbeat_interval: int
        - heartbeat_socket: socket
        - monitor_address: tuple
        + run_detection_loop(): void
        + send_heartbeat(): void
        + simulate_failure(): void
        + detect_obstacles(): void
    }

    HeartbeatMonitor ..> ProcessManager : uses
    ProcessManager --> ObstacleDetector : manages
    ObstacleDetector --> HeartbeatMonitor : sendHeartbeat
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

import sys
from egen.self_healing.monitor import SystemMonitor

if __name__ == "__main__":
    # Optionally accept log_dir and metrics_dir as arguments
    log_dir = sys.argv[1] if len(sys.argv) > 1 else "./logs"
    metrics_dir = sys.argv[2] if len(sys.argv) > 2 else "./metrics"

    monitor = SystemMonitor(log_dir=log_dir, metrics_dir=metrics_dir)
    faults = monitor.check_for_faults()

    if faults:
        print("Detected faults:")
        for fault in faults:
            print(fault)
    else:
        print("No faults detected.") 
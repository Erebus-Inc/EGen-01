"""Self-healing module for the EGen platform.

This module provides components for monitoring the system for faults and
automatically repairing them. It includes:

- SystemMonitor: Monitors logs and metrics for fault patterns
- RepairEngine: Applies repair strategies to detected faults
- SelfHealingAgent: Coordinates monitoring and repair processes
"""

from egen.self_healing.agent import SelfHealingAgent, create_agent
from egen.self_healing.monitor import SystemMonitor
from egen.self_healing.repair import RepairEngine

__all__ = ["SelfHealingAgent", "SystemMonitor", "RepairEngine", "create_agent"]
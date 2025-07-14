"""Self-healing agent for the EGen platform."""

import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

from egen.self_healing.monitor import SystemMonitor
from egen.self_healing.repair import RepairEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SelfHealingAgent:
    """Self-healing agent for the EGen platform.
    
    This class coordinates the SystemMonitor and RepairEngine to detect and repair
    faults in the system automatically.
    """

    def __init__(
        self,
        log_dir: str = "./logs",
        metrics_dir: str = "./metrics",
        log_patterns_path: Optional[str] = None,
        metrics_thresholds_path: Optional[str] = None,
        repair_strategies_path: Optional[str] = None,
        repair_log_path: str = "./logs/repairs.json",
        sandbox_dir: str = "./sandbox",
        enable_web_search: bool = False,
        check_interval: int = 60,  # Check every 60 seconds
    ):
        """Initialize the self-healing agent.
        
        Args:
            log_dir: Directory containing log files to monitor
            metrics_dir: Directory containing metrics data
            log_patterns_path: Path to JSON file containing log patterns to match
            metrics_thresholds_path: Path to JSON file containing metrics thresholds
            repair_strategies_path: Path to JSON file containing repair strategies
            repair_log_path: Path to JSON file for logging repairs
            sandbox_dir: Directory for testing repairs in isolation
            enable_web_search: Whether to enable web search for unknown issues
            check_interval: Interval in seconds between system checks
        """
        # Initialize monitor
        self.monitor = SystemMonitor(
            log_dir=log_dir,
            metrics_dir=metrics_dir,
            log_patterns_path=log_patterns_path,
            metrics_thresholds_path=metrics_thresholds_path,
        )
        
        # Initialize repair engine
        self.repair_engine = RepairEngine(
            repair_strategies_path=repair_strategies_path,
            repair_log_path=repair_log_path,
            sandbox_dir=sandbox_dir,
            enable_web_search=enable_web_search,
        )
        
        # Set check interval
        self.check_interval = check_interval
        
        # Initialize monitoring thread
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
        # Initialize stats
        self.stats = {
            "faults_detected": 0,
            "repairs_attempted": 0,
            "repairs_successful": 0,
            "last_check": None,
        }
    
    def start_monitoring(self) -> None:
        """Start the monitoring thread."""
        if self.monitoring_thread is not None and self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread is already running")
            return
        
        # Reset stop flag
        self.stop_monitoring.clear()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
        )
        self.monitoring_thread.start()
        
        logger.info("Started monitoring thread")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread is not running")
            return
        
        # Set stop flag
        self.stop_monitoring.set()
        
        # Wait for thread to stop
        self.monitoring_thread.join(timeout=5.0)
        
        if self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread did not stop gracefully")
        else:
            logger.info("Stopped monitoring thread")
    
    def _monitoring_loop(self) -> None:
        """Monitoring loop that checks for faults and repairs them."""
        while not self.stop_monitoring.is_set():
            try:
                # Check for faults
                faults = self.check_for_faults()
                
                # Repair faults
                if faults:
                    self.repair_faults(faults)
                
                # Wait for next check
                self.stop_monitoring.wait(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                
                # Wait before retrying
                self.stop_monitoring.wait(self.check_interval)
    
    def check_for_faults(self) -> List[Dict[str, any]]:
        """Check for faults in the system.
        
        Returns:
            List of detected faults
        """
        try:
            # Update stats
            self.stats["last_check"] = datetime.now().isoformat()
            
            # Check for faults
            faults = self.monitor.check_for_faults()
            
            # Update stats
            self.stats["faults_detected"] += len(faults)
            
            return faults
        except Exception as e:
            logger.error(f"Error checking for faults: {e}", exc_info=True)
            return []
    
    def repair_faults(self, faults: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Repair detected faults.
        
        Args:
            faults: List of detected faults
            
        Returns:
            List of repair results
        """
        repair_results = []
        
        for fault in faults:
            try:
                # Update stats
                self.stats["repairs_attempted"] += 1
                
                # Repair fault
                repair_result = self.repair_engine.repair_fault(fault)
                
                # Update stats
                if repair_result["success"]:
                    self.stats["repairs_successful"] += 1
                
                repair_results.append(repair_result)
            except Exception as e:
                logger.error(f"Error repairing fault: {e}", exc_info=True)
        
        return repair_results
    
    def get_stats(self) -> Dict[str, Union[int, str]]:
        """Get monitoring and repair statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.stats


def create_agent(config_path: Optional[str] = None) -> SelfHealingAgent:
    """Create a self-healing agent from a configuration file.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        SelfHealingAgent instance
    """
    # Default configuration
    config = {
        "log_dir": "./logs",
        "metrics_dir": "./metrics",
        "log_patterns_path": None,
        "metrics_thresholds_path": None,
        "repair_strategies_path": None,
        "repair_log_path": "./logs/repairs.json",
        "sandbox_dir": "./sandbox",
        "enable_web_search": False,
        "check_interval": 60,
    }
    
    # Load configuration from file if provided
    if config_path is not None and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
            
            # Update configuration
            config.update(file_config)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
    
    # Create agent
    agent = SelfHealingAgent(**config)
    
    return agent


def main():
    """Main entry point for the self-healing agent."""
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="EGen self-healing agent")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--check-now",
        action="store_true",
        help="Check for faults immediately",
    )
    parser.add_argument(
        "--start-monitoring",
        action="store_true",
        help="Start monitoring thread",
    )
    args = parser.parse_args()
    
    # Create agent
    agent = create_agent(args.config)
    
    # Check for faults if requested
    if args.check_now:
        faults = agent.check_for_faults()
        
        if faults:
            print(f"Found {len(faults)} faults:")
            for fault in faults:
                print(f"- {fault['type']}: {fault['description']}")
            
            # Repair faults
            repair_results = agent.repair_faults(faults)
            
            print(f"\nRepair results:")
            for result in repair_results:
                success = "Success" if result["success"] else "Failed"
                print(f"- {result['fault']['type']}: {success}")
        else:
            print("No faults found")
    
    # Start monitoring if requested
    if args.start_monitoring:
        agent.start_monitoring()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            agent.stop_monitoring()
            
            # Print stats
            stats = agent.get_stats()
            print(f"\nStats:")
            print(f"- Faults detected: {stats['faults_detected']}")
            print(f"- Repairs attempted: {stats['repairs_attempted']}")
            print(f"- Repairs successful: {stats['repairs_successful']}")


if __name__ == "__main__":
    main()
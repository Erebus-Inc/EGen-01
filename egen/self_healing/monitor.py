"""System monitoring for the EGen platform."""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Pattern, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """System monitor for the EGen platform.
    
    This class is responsible for monitoring the system for faults by analyzing
    logs, metrics, and error patterns.
    """

    def __init__(
        self,
        log_dir: str = "./logs",
        metrics_dir: str = "./metrics",
        log_patterns_path: Optional[str] = None,
        metrics_thresholds_path: Optional[str] = None,
    ):
        """Initialize the system monitor.
        
        Args:
            log_dir: Directory containing log files to monitor
            metrics_dir: Directory containing metrics data
            log_patterns_path: Path to JSON file containing log patterns to match
            metrics_thresholds_path: Path to JSON file containing metrics thresholds
        """
        self.log_dir = log_dir
        self.metrics_dir = metrics_dir
        
        # Load log patterns
        self.log_patterns = self._load_log_patterns(log_patterns_path)
        
        # Load metrics thresholds
        self.metrics_thresholds = self._load_metrics_thresholds(metrics_thresholds_path)
        
        # Compiled regex patterns
        self.compiled_patterns = self._compile_patterns()
    
    def _load_log_patterns(self, path: Optional[str]) -> Dict[str, Dict[str, str]]:
        """Load log patterns from a JSON file.
        
        If path is None or the file doesn't exist, return default patterns.
        
        Args:
            path: Path to JSON file containing log patterns
            
        Returns:
            Dictionary mapping fault types to pattern dictionaries
        """
        default_patterns = {
            "out_of_memory": {
                "pattern": r"(OutOfMemoryError|MemoryError|Killed|Out of memory)",
                "description": "Out of memory error",
                "severity": "critical",
            },
            "cuda_error": {
                "pattern": r"(CUDA error|CUDA out of memory|CUDA_ERROR|CudaError)",
                "description": "CUDA error",
                "severity": "critical",
            },
            "training_divergence": {
                "pattern": r"(Loss is nan|Loss is inf|Gradient overflow|Diverging loss)",
                "description": "Training divergence",
                "severity": "high",
            },
            "file_not_found": {
                "pattern": r"(FileNotFoundError|No such file or directory)",
                "description": "File not found",
                "severity": "medium",
            },
            "permission_error": {
                "pattern": r"(PermissionError|Permission denied)",
                "description": "Permission error",
                "severity": "medium",
            },
            "network_error": {
                "pattern": r"(ConnectionError|ConnectionRefusedError|ConnectionResetError|TimeoutError)",
                "description": "Network error",
                "severity": "medium",
            },
            "import_error": {
                "pattern": r"(ImportError|ModuleNotFoundError)",
                "description": "Import error",
                "severity": "medium",
            },
        }
        
        if path is None or not os.path.exists(path):
            return default_patterns
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                patterns = json.load(f)
            return patterns
        except Exception as e:
            logger.error(f"Error loading log patterns: {e}", exc_info=True)
            return default_patterns
    
    def _load_metrics_thresholds(self, path: Optional[str]) -> Dict[str, Dict[str, Union[float, str]]]:
        """Load metrics thresholds from a JSON file.
        
        If path is None or the file doesn't exist, return default thresholds.
        
        Args:
            path: Path to JSON file containing metrics thresholds
            
        Returns:
            Dictionary mapping metric names to threshold dictionaries
        """
        default_thresholds = {
            "gpu_memory_usage": {
                "warning": 0.8,  # 80%
                "critical": 0.95,  # 95%
                "description": "GPU memory usage",
                "severity": "high",
            },
            "cpu_memory_usage": {
                "warning": 0.8,  # 80%
                "critical": 0.95,  # 95%
                "description": "CPU memory usage",
                "severity": "high",
            },
            "gpu_utilization": {
                "warning": 0.95,  # 95%
                "critical": 0.99,  # 99%
                "description": "GPU utilization",
                "severity": "medium",
            },
            "cpu_utilization": {
                "warning": 0.9,  # 90%
                "critical": 0.95,  # 95%
                "description": "CPU utilization",
                "severity": "medium",
            },
            "disk_usage": {
                "warning": 0.8,  # 80%
                "critical": 0.95,  # 95%
                "description": "Disk usage",
                "severity": "medium",
            },
            "training_loss": {
                "warning": 100.0,
                "critical": 1000.0,
                "description": "Training loss",
                "severity": "high",
            },
            "validation_loss": {
                "warning": 100.0,
                "critical": 1000.0,
                "description": "Validation loss",
                "severity": "high",
            },
            "error_rate": {
                "warning": 0.1,  # 10%
                "critical": 0.3,  # 30%
                "description": "Error rate",
                "severity": "high",
            },
            "latency": {
                "warning": 1.0,  # 1 second
                "critical": 5.0,  # 5 seconds
                "description": "API latency",
                "severity": "medium",
            },
        }
        
        if path is None or not os.path.exists(path):
            return default_thresholds
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                thresholds = json.load(f)
            return thresholds
        except Exception as e:
            logger.error(f"Error loading metrics thresholds: {e}", exc_info=True)
            return default_thresholds
    
    def _compile_patterns(self) -> Dict[str, Pattern]:
        """Compile regex patterns for log analysis.
        
        Returns:
            Dictionary mapping fault types to compiled regex patterns
        """
        compiled_patterns = {}
        
        for fault_type, pattern_dict in self.log_patterns.items():
            try:
                compiled_patterns[fault_type] = re.compile(
                    pattern_dict["pattern"], re.IGNORECASE
                )
            except re.error as e:
                logger.error(
                    f"Error compiling pattern for {fault_type}: {e}", exc_info=True
                )
        
        return compiled_patterns
    
    def check_for_faults(self) -> List[Dict[str, any]]:
        """Check for faults in the system.
        
        Returns:
            List of detected faults as dictionaries
        """
        faults = []
        
        # Check logs for errors
        log_faults = self._check_logs()
        faults.extend(log_faults)
        
        # Check metrics for anomalies
        metric_faults = self._check_metrics()
        faults.extend(metric_faults)
        
        return faults
    
    def _check_logs(self) -> List[Dict[str, any]]:
        """Check log files for error patterns.
        
        Returns:
            List of detected faults from logs
        """
        faults = []
        
        # Get log files modified in the last day
        log_files = self._get_recent_log_files()
        
        for log_file in log_files:
            file_faults = self._analyze_log_file(log_file)
            faults.extend(file_faults)
        
        return faults
    
    def _get_recent_log_files(self) -> List[str]:
        """Get log files modified in the last day.
        
        Returns:
            List of paths to recent log files
        """
        recent_files = []
        
        if not os.path.exists(self.log_dir):
            return recent_files
        
        # Get current time
        now = datetime.now()
        
        # Get all files in log directory
        for root, _, files in os.walk(self.log_dir):
            for file in files:
                if not file.endswith(".log"):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Check if file was modified in the last day
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if now - mtime <= timedelta(days=1):
                        recent_files.append(file_path)
                except OSError:
                    continue
        
        return recent_files
    
    def _analyze_log_file(self, log_file: str) -> List[Dict[str, any]]:
        """Analyze a log file for error patterns.
        
        Args:
            log_file: Path to log file
            
        Returns:
            List of detected faults from the log file
        """
        faults = []
        
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                log_content = f.read()
            
            # Check each pattern
            for fault_type, pattern in self.compiled_patterns.items():
                matches = pattern.findall(log_content)
                
                if matches:
                    # Create fault entry
                    fault = {
                        "type": fault_type,
                        "source": "log",
                        "file": log_file,
                        "matches": matches,
                        "timestamp": datetime.now().isoformat(),
                        "description": self.log_patterns[fault_type]["description"],
                        "severity": self.log_patterns[fault_type]["severity"],
                    }
                    
                    faults.append(fault)
        except Exception as e:
            logger.error(f"Error analyzing log file {log_file}: {e}", exc_info=True)
        
        return faults
    
    def _check_metrics(self) -> List[Dict[str, any]]:
        """Check metrics for anomalies.
        
        Returns:
            List of detected faults from metrics
        """
        faults = []
        
        # Get metric files
        metric_files = self._get_metric_files()
        
        for metric_file in metric_files:
            file_faults = self._analyze_metric_file(metric_file)
            faults.extend(file_faults)
        
        return faults
    
    def _get_metric_files(self) -> List[str]:
        """Get metric files.
        
        Returns:
            List of paths to metric files
        """
        metric_files = []
        
        if not os.path.exists(self.metrics_dir):
            return metric_files
        
        # Get all files in metrics directory
        for root, _, files in os.walk(self.metrics_dir):
            for file in files:
                if not file.endswith(".json"):
                    continue
                
                file_path = os.path.join(root, file)
                metric_files.append(file_path)
        
        return metric_files
    
    def _analyze_metric_file(self, metric_file: str) -> List[Dict[str, any]]:
        """Analyze a metric file for anomalies.
        
        Args:
            metric_file: Path to metric file
            
        Returns:
            List of detected faults from the metric file
        """
        faults = []
        
        try:
            with open(metric_file, "r", encoding="utf-8") as f:
                metrics = json.load(f)
            
            # Check each metric against thresholds
            for metric_name, metric_value in metrics.items():
                if metric_name not in self.metrics_thresholds:
                    continue
                
                threshold = self.metrics_thresholds[metric_name]
                
                # Check if metric exceeds critical threshold
                if metric_value > threshold["critical"]:
                    fault = {
                        "type": f"{metric_name}_critical",
                        "source": "metric",
                        "file": metric_file,
                        "value": metric_value,
                        "threshold": threshold["critical"],
                        "timestamp": datetime.now().isoformat(),
                        "description": f"{threshold['description']} critical",
                        "severity": threshold["severity"],
                    }
                    
                    faults.append(fault)
                # Check if metric exceeds warning threshold
                elif metric_value > threshold["warning"]:
                    fault = {
                        "type": f"{metric_name}_warning",
                        "source": "metric",
                        "file": metric_file,
                        "value": metric_value,
                        "threshold": threshold["warning"],
                        "timestamp": datetime.now().isoformat(),
                        "description": f"{threshold['description']} warning",
                        "severity": "low",
                    }
                    
                    faults.append(fault)
        except Exception as e:
            logger.error(f"Error analyzing metric file {metric_file}: {e}", exc_info=True)
        
        return faults
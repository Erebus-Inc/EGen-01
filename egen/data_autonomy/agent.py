"""Data autonomy agent for the EGen platform.

This module provides the main agent that coordinates
data collection, processing, validation, and management.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    logging.warning("Schedule not available. Install with: pip install schedule")

from .collector import DataCollector
from .processor import DataProcessor
from .validator import DataValidator
from .manager import DataManager

# --- Stage 2: Data Autonomy Engine Extensions ---
try:
    from datasets import list_datasets, load_dataset
except ImportError:
    list_datasets = None
    load_dataset = None
import requests

class DatasetSearcher:
    """Searches Hugging Face Hub for datasets and retrieves them."""
    def search(self, query: str, max_results: int = 10):
        if list_datasets is None:
            logger.warning("datasets library not installed.")
            return []
        all_datasets = list_datasets()
        return [ds for ds in all_datasets if query.lower() in ds.lower()][:max_results]
    def retrieve(self, name: str, split: str = "train"):
        if load_dataset is None:
            logger.warning("datasets library not installed.")
            return None
        try:
            return load_dataset(name, split=split)
        except Exception as e:
            logger.error(f"Error loading dataset {name}: {e}")
            return None

class WebCorpusCrawler:
    """Crawls web for open-source corpora (simple DuckDuckGo HTML parser)."""
    def crawl(self, topic: str, max_results: int = 5):
        url = f"https://duckduckgo.com/html/?q={topic}+open+corpus"
        try:
            resp = requests.get(url, timeout=10)
            links = []
            for line in resp.text.split('\n'):
                if 'href="' in line:
                    start = line.find('href="') + 6
                    end = line.find('"', start)
                    link = line[start:end]
                    if link.startswith('http'):
                        links.append(link)
                    if len(links) >= max_results:
                        break
            return links
        except Exception as e:
            logger.error(f"Web crawling error: {e}")
            return []

class ContinuousLearner:
    """Handles continuous learning with versioned datasets."""
    def __init__(self):
        self.versions = []
    def update(self, dataset):
        version = {"timestamp": datetime.now().isoformat(), "size": len(dataset) if hasattr(dataset, '__len__') else None}
        self.versions.append(version)
    def get_versions(self):
        return self.versions

class DataQualityAssessor:
    """Assesses data quality and detects bias."""
    def assess(self, dataset):
        # Simple quality: check for duplicates and missing values
        if hasattr(dataset, "to_pandas"):
            df = dataset.to_pandas()
            duplicates = df.duplicated().sum()
            missing = df.isnull().sum().sum()
            bias = self.detect_bias(df)
            return {"duplicates": duplicates, "missing": missing, "bias": bias}
        return {"duplicates": None, "missing": None, "bias": None}
    def detect_bias(self, df):
        # Simple class imbalance check for 'label' column
        if "label" in df.columns:
            counts = df["label"].value_counts()
            if counts.max() > 2 * counts.min():
                return True
        return False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DataAutonomyAgent:
    """Data autonomy agent for the EGen platform.
    
    This agent coordinates data collection, processing,
    validation, and management for autonomous data operations.
    """

    def __init__(
        self,
        config_path: str = "./data_autonomy_config.json",
        data_dir: str = "./data_repository",
        logs_dir: str = "./logs/data_autonomy",
        enable_scheduling: bool = True,
        enable_continuous_learning: bool = True,
        max_workers: int = 4,
        monitoring_interval: int = 300,  # 5 minutes
        auto_validation: bool = True,
        auto_processing: bool = True,
        quality_threshold: float = 0.7
    ):
        """Initialize the data autonomy agent.
        
        Args:
            config_path: Path to configuration file
            data_dir: Directory for data storage
            logs_dir: Directory for logs
            enable_scheduling: Whether to enable scheduled operations
            enable_continuous_learning: Whether to enable continuous learning
            max_workers: Maximum number of worker threads
            monitoring_interval: Monitoring interval in seconds
            auto_validation: Whether to automatically validate data
            auto_processing: Whether to automatically process data
            quality_threshold: Minimum quality threshold for data
        """
        self.config_path = config_path
        self.data_dir = Path(data_dir)
        self.logs_dir = Path(logs_dir)
        self.enable_scheduling = enable_scheduling and SCHEDULE_AVAILABLE
        self.enable_continuous_learning = enable_continuous_learning
        self.max_workers = max_workers
        self.monitoring_interval = monitoring_interval
        self.auto_validation = auto_validation
        self.auto_processing = auto_processing
        self.quality_threshold = quality_threshold
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.collector = DataCollector(
            cache_dir=str(self.data_dir / "cache"),
            enable_caching=True
        )
        
        self.processor = DataProcessor(
            enable_augmentation=True,
            enable_filtering=True,
            save_processed=True
        )
        
        self.validator = DataValidator(
            reports_dir=str(self.logs_dir / "validation_reports")
        )
        
        self.manager = DataManager(
            data_dir=str(self.data_dir),
            metadata_db=str(self.data_dir / "metadata.db"),
            enable_versioning=True,
            enable_compression=True,
            auto_cleanup=True
        )
        
        # Load configuration
        self.config = self._load_config()
        
        # Agent state
        self.is_running = False
        self.last_collection_time = None
        self.last_processing_time = None
        self.last_validation_time = None
        
        # Statistics
        self.agent_stats = {
            "start_time": None,
            "uptime_seconds": 0,
            "collections_performed": 0,
            "datasets_processed": 0,
            "validations_completed": 0,
            "quality_issues_detected": 0,
            "autonomous_actions_taken": 0,
            "last_activity": None,
            "errors_encountered": 0
        }
        
        # Learning memory
        self.learning_memory = {
            "successful_sources": set(),
            "failed_sources": set(),
            "quality_patterns": {},
            "processing_preferences": {},
            "validation_insights": {}
        }
        
        # Setup logging
        self._setup_logging()
        
        logger.info("Data Autonomy Agent initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        default_config = {
            "collection": {
                "sources": {
                    "huggingface": {
                        "enabled": True,
                        "search_queries": [
                            "text classification",
                            "sentiment analysis",
                            "question answering",
                            "language modeling"
                        ],
                        "max_datasets": 10,
                        "min_downloads": 100
                    },
                    "web_crawling": {
                        "enabled": False,
                        "urls": [],
                        "max_depth": 2,
                        "rate_limit": 1.0
                    },
                    "local_directories": {
                        "enabled": True,
                        "paths": ["./datasets", "./data"]
                    }
                },
                "schedule": {
                    "enabled": True,
                    "interval_hours": 24,
                    "max_collections_per_day": 5
                }
            },
            "processing": {
                "tokenizer_name": "bert-base-uncased",
                "max_length": 512,
                "augmentation": {
                    "enabled": True,
                    "techniques": ["synonym_replacement", "random_insertion"],
                    "augmentation_ratio": 0.1
                },
                "filtering": {
                    "enabled": True,
                    "min_length": 10,
                    "max_length": 1000,
                    "remove_duplicates": True
                }
            },
            "validation": {
                "quality_checks": {
                    "completeness": True,
                    "uniqueness": True,
                    "consistency": True,
                    "validity": True
                },
                "bias_detection": {
                    "enabled": True,
                    "categories": ["gender", "race", "age", "religion"]
                },
                "quality_threshold": 0.7,
                "auto_reject_threshold": 0.3
            },
            "management": {
                "versioning": {
                    "enabled": True,
                    "max_versions": 10
                },
                "storage": {
                    "compression": True,
                    "limit_gb": 100.0,
                    "auto_cleanup": True
                },
                "backup": {
                    "enabled": True,
                    "interval_hours": 168,  # Weekly
                    "retention_days": 30
                }
            },
            "learning": {
                "enabled": True,
                "memory_size": 1000,
                "adaptation_rate": 0.1,
                "quality_feedback_weight": 0.8
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with defaults
                return self._merge_configs(default_config, config)
            else:
                # Save default config
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return default_config
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Merge custom config with default config.
        
        Args:
            default: Default configuration
            custom: Custom configuration
            
        Returns:
            Merged configuration
        """
        merged = default.copy()
        
        for key, value in custom.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _setup_logging(self) -> None:
        """Setup logging for the agent."""
        try:
            # Create file handler
            log_file = self.logs_dir / "data_autonomy_agent.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    def start(self) -> None:
        """Start the data autonomy agent."""
        if self.is_running:
            logger.warning("Agent is already running")
            return
        
        logger.info("Starting Data Autonomy Agent")
        
        self.is_running = True
        self.agent_stats["start_time"] = datetime.now().isoformat()
        
        # Setup scheduling if enabled
        if self.enable_scheduling:
            self._setup_scheduling()
        
        # Start monitoring loop
        self._start_monitoring()
    
    def stop(self) -> None:
        """Stop the data autonomy agent."""
        if not self.is_running:
            logger.warning("Agent is not running")
            return
        
        logger.info("Stopping Data Autonomy Agent")
        
        self.is_running = False
        
        # Calculate uptime
        if self.agent_stats["start_time"]:
            start_time = datetime.fromisoformat(self.agent_stats["start_time"])
            uptime = datetime.now() - start_time
            self.agent_stats["uptime_seconds"] = uptime.total_seconds()
        
        logger.info(f"Agent stopped. Uptime: {self.agent_stats['uptime_seconds']:.2f} seconds")
    
    def _setup_scheduling(self) -> None:
        """Setup scheduled operations."""
        try:
            if not SCHEDULE_AVAILABLE:
                logger.warning("Schedule library not available, skipping scheduling setup")
                return
            
            # Schedule data collection
            collection_config = self.config.get("collection", {}).get("schedule", {})
            if collection_config.get("enabled", True):
                interval_hours = collection_config.get("interval_hours", 24)
                schedule.every(interval_hours).hours.do(self._scheduled_collection)
                logger.info(f"Scheduled data collection every {interval_hours} hours")
            
            # Schedule backup
            backup_config = self.config.get("management", {}).get("backup", {})
            if backup_config.get("enabled", True):
                interval_hours = backup_config.get("interval_hours", 168)
                schedule.every(interval_hours).hours.do(self._scheduled_backup)
                logger.info(f"Scheduled backup every {interval_hours} hours")
            
        except Exception as e:
            logger.error(f"Error setting up scheduling: {e}", exc_info=True)
    
    def _start_monitoring(self) -> None:
        """Start the monitoring loop."""
        logger.info("Starting monitoring loop")
        
        while self.is_running:
            try:
                # Run scheduled tasks
                if self.enable_scheduling and SCHEDULE_AVAILABLE:
                    schedule.run_pending()
                
                # Perform autonomous operations
                self._autonomous_operations()
                
                # Update statistics
                self._update_statistics()
                
                # Sleep for monitoring interval
                time.sleep(self.monitoring_interval)
            
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping agent")
                self.stop()
                break
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                self.agent_stats["errors_encountered"] += 1
                time.sleep(self.monitoring_interval)
    
    def _autonomous_operations(self) -> None:
        """Perform autonomous operations."""
        try:
            # Check for new data to collect
            if self._should_collect_data():
                self._autonomous_collection()
            
            # Check for data to process
            if self._should_process_data():
                self._autonomous_processing()
            
            # Check for data to validate
            if self._should_validate_data():
                self._autonomous_validation()
            
            # Perform continuous learning
            if self.enable_continuous_learning:
                self._continuous_learning()
        
        except Exception as e:
            logger.error(f"Error in autonomous operations: {e}", exc_info=True)
    
    def _should_collect_data(self) -> bool:
        """Check if data collection should be performed.
        
        Returns:
            True if collection should be performed
        """
        # Check if enough time has passed since last collection
        if self.last_collection_time:
            time_since_last = datetime.now() - self.last_collection_time
            min_interval = timedelta(hours=1)  # Minimum 1 hour between collections
            if time_since_last < min_interval:
                return False
        
        # Check daily collection limit
        collection_config = self.config.get("collection", {}).get("schedule", {})
        max_collections = collection_config.get("max_collections_per_day", 5)
        
        # Simple check - could be enhanced with proper daily tracking
        if self.agent_stats["collections_performed"] >= max_collections:
            return False
        
        return True
    
    def _should_process_data(self) -> bool:
        """Check if data processing should be performed.
        
        Returns:
            True if processing should be performed
        """
        if not self.auto_processing:
            return False
        
        # Check for unprocessed datasets
        datasets = self.manager.list_datasets()
        for dataset in datasets:
            metadata = dataset.get("metadata", {})
            if not metadata.get("processed", False):
                return True
        
        return False
    
    def _should_validate_data(self) -> bool:
        """Check if data validation should be performed.
        
        Returns:
            True if validation should be performed
        """
        if not self.auto_validation:
            return False
        
        # Check for unvalidated datasets
        datasets = self.manager.list_datasets()
        for dataset in datasets:
            metadata = dataset.get("metadata", {})
            if not metadata.get("validated", False):
                return True
        
        return False
    
    def _autonomous_collection(self) -> None:
        """Perform autonomous data collection."""
        logger.info("Performing autonomous data collection")
        
        try:
            collection_config = self.config.get("collection", {})
            sources_config = collection_config.get("sources", {})
            
            collected_datasets = []
            
            # Collect from Hugging Face
            hf_config = sources_config.get("huggingface", {})
            if hf_config.get("enabled", True):
                hf_datasets = self._collect_from_huggingface(hf_config)
                collected_datasets.extend(hf_datasets)
            
            # Collect from local directories
            local_config = sources_config.get("local_directories", {})
            if local_config.get("enabled", True):
                local_datasets = self._collect_from_local(local_config)
                collected_datasets.extend(local_datasets)
            
            # Store collected datasets
            for dataset_info in collected_datasets:
                self._store_collected_dataset(dataset_info)
            
            self.agent_stats["collections_performed"] += 1
            self.agent_stats["autonomous_actions_taken"] += 1
            self.last_collection_time = datetime.now()
            
            logger.info(f"Autonomous collection completed. Collected {len(collected_datasets)} datasets")
        
        except Exception as e:
            logger.error(f"Error in autonomous collection: {e}", exc_info=True)
            self.agent_stats["errors_encountered"] += 1
    
    def _collect_from_huggingface(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect datasets from Hugging Face.
        
        Args:
            config: Hugging Face collection configuration
            
        Returns:
            List of collected dataset information
        """
        collected = []
        
        try:
            search_queries = config.get("search_queries", [])
            max_datasets = config.get("max_datasets", 10)
            min_downloads = config.get("min_downloads", 100)
            
            for query in search_queries:
                # Use learning memory to prioritize successful sources
                if query in self.learning_memory["failed_sources"]:
                    logger.info(f"Skipping query '{query}' due to previous failures")
                    continue
                
                try:
                    datasets = self.collector.search_huggingface_datasets(
                        query=query,
                        limit=max_datasets // len(search_queries),
                        min_downloads=min_downloads
                    )
                    
                    for dataset in datasets:
                        # Download dataset
                        download_result = self.collector.download_huggingface_dataset(
                            dataset_name=dataset["id"],
                            subset=None,
                            split="train"
                        )
                        
                        if download_result["success"]:
                            collected.append({
                                "name": dataset["id"],
                                "source": "huggingface",
                                "query": query,
                                "data": download_result["data"],
                                "metadata": {
                                    "description": dataset.get("description", ""),
                                    "downloads": dataset.get("downloads", 0),
                                    "tags": dataset.get("tags", []),
                                    "original_metadata": dataset
                                }
                            })
                            
                            # Update learning memory
                            self.learning_memory["successful_sources"].add(query)
                        else:
                            logger.warning(f"Failed to download dataset {dataset['id']}")
                
                except Exception as e:
                    logger.error(f"Error collecting from query '{query}': {e}")
                    self.learning_memory["failed_sources"].add(query)
        
        except Exception as e:
            logger.error(f"Error in Hugging Face collection: {e}", exc_info=True)
        
        return collected
    
    def _collect_from_local(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect datasets from local directories.
        
        Args:
            config: Local collection configuration
            
        Returns:
            List of collected dataset information
        """
        collected = []
        
        try:
            paths = config.get("paths", [])
            
            for path in paths:
                if not os.path.exists(path):
                    continue
                
                try:
                    datasets = self.collector.scan_local_directory(path)
                    
                    for dataset in datasets:
                        collected.append({
                            "name": dataset["name"],
                            "source": "local",
                            "path": path,
                            "data": dataset["file_path"],  # File path for local data
                            "metadata": {
                                "description": f"Local dataset from {path}",
                                "file_info": dataset
                            }
                        })
                
                except Exception as e:
                    logger.error(f"Error collecting from local path '{path}': {e}")
        
        except Exception as e:
            logger.error(f"Error in local collection: {e}", exc_info=True)
        
        return collected
    
    def _store_collected_dataset(self, dataset_info: Dict[str, Any]) -> None:
        """Store a collected dataset.
        
        Args:
            dataset_info: Dataset information
        """
        try:
            # Generate unique dataset name
            base_name = dataset_info["name"].replace("/", "_").replace(" ", "_")
            dataset_name = f"{base_name}_{dataset_info['source']}"
            
            # Store dataset
            storage_result = self.manager.store_dataset(
                data=dataset_info["data"],
                dataset_name=dataset_name,
                description=dataset_info["metadata"].get("description", ""),
                source=dataset_info["source"],
                tags=[dataset_info["source"], "autonomous_collection"],
                metadata=dataset_info["metadata"]
            )
            
            if storage_result["success"]:
                logger.info(f"Stored dataset: {dataset_name}")
            else:
                logger.error(f"Failed to store dataset: {dataset_name}")
        
        except Exception as e:
            logger.error(f"Error storing collected dataset: {e}", exc_info=True)
    
    def _autonomous_processing(self) -> None:
        """Perform autonomous data processing."""
        logger.info("Performing autonomous data processing")
        
        try:
            # Get unprocessed datasets
            datasets = self.manager.list_datasets()
            unprocessed = [
                d for d in datasets 
                if not d.get("metadata", {}).get("processed", False)
            ]
            
            processing_config = self.config.get("processing", {})
            
            # Process datasets in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for dataset in unprocessed[:5]:  # Limit to 5 datasets per batch
                    future = executor.submit(
                        self._process_single_dataset,
                        dataset,
                        processing_config
                    )
                    futures.append(future)
                
                # Wait for completion
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result["success"]:
                            self.agent_stats["datasets_processed"] += 1
                    except Exception as e:
                        logger.error(f"Error in dataset processing: {e}")
                        self.agent_stats["errors_encountered"] += 1
            
            self.agent_stats["autonomous_actions_taken"] += 1
            self.last_processing_time = datetime.now()
            
            logger.info(f"Autonomous processing completed. Processed {len(unprocessed)} datasets")
        
        except Exception as e:
            logger.error(f"Error in autonomous processing: {e}", exc_info=True)
            self.agent_stats["errors_encountered"] += 1
    
    def _process_single_dataset(
        self,
        dataset: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single dataset.
        
        Args:
            dataset: Dataset metadata
            config: Processing configuration
            
        Returns:
            Processing result
        """
        result = {"success": False, "dataset_name": dataset["name"]}
        
        try:
            # Retrieve dataset
            retrieval_result = self.manager.retrieve_dataset(dataset["name"])
            
            if not retrieval_result["success"]:
                result["error"] = "Failed to retrieve dataset"
                return result
            
            # Process dataset
            processing_result = self.processor.process_dataset(
                data=retrieval_result["data"],
                dataset_name=dataset["name"],
                tokenizer_name=config.get("tokenizer_name", "bert-base-uncased"),
                max_length=config.get("max_length", 512),
                enable_augmentation=config.get("augmentation", {}).get("enabled", True),
                enable_filtering=config.get("filtering", {}).get("enabled", True)
            )
            
            if processing_result["success"]:
                # Update dataset metadata to mark as processed
                updated_metadata = dataset.get("metadata", {})
                updated_metadata["processed"] = True
                updated_metadata["processing_stats"] = processing_result["statistics"]
                
                # Store processed dataset
                storage_result = self.manager.store_dataset(
                    data=processing_result["processed_data"],
                    dataset_name=f"{dataset['name']}_processed",
                    description=f"Processed version of {dataset['name']}",
                    source=dataset.get("source", "unknown"),
                    tags=dataset.get("tags", []) + ["processed"],
                    metadata=updated_metadata,
                    force_update=True
                )
                
                result["success"] = storage_result["success"]
                result["processing_stats"] = processing_result["statistics"]
            
            else:
                result["error"] = processing_result.get("error", "Processing failed")
        
        except Exception as e:
            logger.error(f"Error processing dataset {dataset['name']}: {e}")
            result["error"] = str(e)
        
        return result
    
    def _autonomous_validation(self) -> None:
        """Perform autonomous data validation."""
        logger.info("Performing autonomous data validation")
        
        try:
            # Get unvalidated datasets
            datasets = self.manager.list_datasets()
            unvalidated = [
                d for d in datasets 
                if not d.get("metadata", {}).get("validated", False)
            ]
            
            validation_config = self.config.get("validation", {})
            
            for dataset in unvalidated[:5]:  # Limit to 5 datasets per batch
                try:
                    validation_result = self._validate_single_dataset(
                        dataset,
                        validation_config
                    )
                    
                    if validation_result["success"]:
                        self.agent_stats["validations_completed"] += 1
                        
                        # Check quality threshold
                        quality_score = validation_result.get("quality_score", 0)
                        if quality_score < self.quality_threshold:
                            self.agent_stats["quality_issues_detected"] += 1
                            
                            # Auto-reject if below auto-reject threshold
                            auto_reject_threshold = validation_config.get("auto_reject_threshold", 0.3)
                            if quality_score < auto_reject_threshold:
                                logger.warning(f"Auto-rejecting dataset {dataset['name']} due to low quality: {quality_score}")
                                self.manager.delete_dataset(dataset["name"])
                    
                except Exception as e:
                    logger.error(f"Error validating dataset {dataset['name']}: {e}")
                    self.agent_stats["errors_encountered"] += 1
            
            self.agent_stats["autonomous_actions_taken"] += 1
            self.last_validation_time = datetime.now()
            
            logger.info(f"Autonomous validation completed. Validated {len(unvalidated)} datasets")
        
        except Exception as e:
            logger.error(f"Error in autonomous validation: {e}", exc_info=True)
            self.agent_stats["errors_encountered"] += 1
    
    def _validate_single_dataset(
        self,
        dataset: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single dataset.
        
        Args:
            dataset: Dataset metadata
            config: Validation configuration
            
        Returns:
            Validation result
        """
        result = {"success": False, "dataset_name": dataset["name"]}
        
        try:
            # Retrieve dataset
            retrieval_result = self.manager.retrieve_dataset(dataset["name"])
            
            if not retrieval_result["success"]:
                result["error"] = "Failed to retrieve dataset"
                return result
            
            # Validate dataset
            validation_result = self.validator.validate_dataset(
                data=retrieval_result["data"],
                dataset_name=dataset["name"]
            )
            
            if validation_result["success"]:
                # Update dataset metadata to mark as validated
                updated_metadata = dataset.get("metadata", {})
                updated_metadata["validated"] = True
                updated_metadata["validation_report"] = validation_result["report"]
                updated_metadata["quality_score"] = validation_result["report"]["overall_score"]
                
                # Store updated metadata
                storage_result = self.manager.store_dataset(
                    data=retrieval_result["data"],
                    dataset_name=dataset["name"],
                    description=dataset.get("description", ""),
                    source=dataset.get("source", "unknown"),
                    tags=dataset.get("tags", []) + ["validated"],
                    metadata=updated_metadata,
                    force_update=True
                )
                
                result["success"] = storage_result["success"]
                result["quality_score"] = validation_result["report"]["overall_score"]
                result["validation_report"] = validation_result["report"]
            
            else:
                result["error"] = validation_result.get("error", "Validation failed")
        
        except Exception as e:
            logger.error(f"Error validating dataset {dataset['name']}: {e}")
            result["error"] = str(e)
        
        return result
    
    def _continuous_learning(self) -> None:
        """Perform continuous learning operations."""
        try:
            learning_config = self.config.get("learning", {})
            
            if not learning_config.get("enabled", True):
                return
            
            # Analyze recent validation results for patterns
            self._analyze_quality_patterns()
            
            # Update processing preferences based on success rates
            self._update_processing_preferences()
            
            # Adapt collection strategies
            self._adapt_collection_strategies()
            
            # Prune learning memory if it gets too large
            memory_size = learning_config.get("memory_size", 1000)
            self._prune_learning_memory(memory_size)
        
        except Exception as e:
            logger.error(f"Error in continuous learning: {e}", exc_info=True)
    
    def _analyze_quality_patterns(self) -> None:
        """Analyze quality patterns from validation results."""
        try:
            # Get recent datasets with validation results
            datasets = self.manager.list_datasets(limit=100)
            
            for dataset in datasets:
                metadata = dataset.get("metadata", {})
                if "validation_report" in metadata:
                    report = metadata["validation_report"]
                    source = dataset.get("source", "unknown")
                    
                    # Track quality by source
                    if source not in self.learning_memory["quality_patterns"]:
                        self.learning_memory["quality_patterns"][source] = []
                    
                    self.learning_memory["quality_patterns"][source].append(
                        report.get("overall_score", 0)
                    )
                    
                    # Keep only recent scores
                    if len(self.learning_memory["quality_patterns"][source]) > 50:
                        self.learning_memory["quality_patterns"][source] = \
                            self.learning_memory["quality_patterns"][source][-50:]
        
        except Exception as e:
            logger.error(f"Error analyzing quality patterns: {e}")
    
    def _update_processing_preferences(self) -> None:
        """Update processing preferences based on success rates."""
        try:
            # Analyze processing success rates
            datasets = self.manager.list_datasets(limit=100)
            
            processing_stats = {}
            
            for dataset in datasets:
                metadata = dataset.get("metadata", {})
                if "processing_stats" in metadata:
                    stats = metadata["processing_stats"]
                    
                    # Track processing techniques and their outcomes
                    for technique, success in stats.items():
                        if technique not in processing_stats:
                            processing_stats[technique] = []
                        processing_stats[technique].append(success)
            
            # Update preferences based on success rates
            for technique, outcomes in processing_stats.items():
                if len(outcomes) >= 5:  # Minimum sample size
                    success_rate = sum(outcomes) / len(outcomes)
                    self.learning_memory["processing_preferences"][technique] = success_rate
        
        except Exception as e:
            logger.error(f"Error updating processing preferences: {e}")
    
    def _adapt_collection_strategies(self) -> None:
        """Adapt collection strategies based on learning."""
        try:
            # Analyze source quality patterns
            for source, scores in self.learning_memory["quality_patterns"].items():
                if len(scores) >= 10:  # Minimum sample size
                    avg_quality = sum(scores) / len(scores)
                    
                    # If average quality is low, add to failed sources
                    if avg_quality < 0.5:
                        self.learning_memory["failed_sources"].add(source)
                        logger.info(f"Marking source '{source}' as low quality (avg: {avg_quality:.2f})")
                    
                    # If average quality is high, ensure it's in successful sources
                    elif avg_quality > 0.8:
                        self.learning_memory["successful_sources"].add(source)
                        # Remove from failed sources if present
                        self.learning_memory["failed_sources"].discard(source)
        
        except Exception as e:
            logger.error(f"Error adapting collection strategies: {e}")
    
    def _prune_learning_memory(self, max_size: int) -> None:
        """Prune learning memory to keep it within size limits.
        
        Args:
            max_size: Maximum size for each memory component
        """
        try:
            # Prune successful sources
            if len(self.learning_memory["successful_sources"]) > max_size:
                # Keep most recent (convert to list, sort, convert back)
                sources_list = list(self.learning_memory["successful_sources"])
                self.learning_memory["successful_sources"] = set(sources_list[-max_size:])
            
            # Prune failed sources
            if len(self.learning_memory["failed_sources"]) > max_size:
                sources_list = list(self.learning_memory["failed_sources"])
                self.learning_memory["failed_sources"] = set(sources_list[-max_size:])
            
            # Prune quality patterns
            for source in list(self.learning_memory["quality_patterns"].keys()):
                scores = self.learning_memory["quality_patterns"][source]
                if len(scores) > max_size:
                    self.learning_memory["quality_patterns"][source] = scores[-max_size:]
        
        except Exception as e:
            logger.error(f"Error pruning learning memory: {e}")
    
    def _scheduled_collection(self) -> None:
        """Scheduled data collection task."""
        logger.info("Running scheduled data collection")
        
        if self._should_collect_data():
            self._autonomous_collection()
        else:
            logger.info("Skipping scheduled collection (conditions not met)")
    
    def _scheduled_backup(self) -> None:
        """Scheduled backup task."""
        logger.info("Running scheduled backup")
        
        try:
            backup_path = self.logs_dir / f"metadata_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            if self.manager.backup_metadata(str(backup_path)):
                logger.info(f"Backup completed: {backup_path}")
                
                # Clean old backups
                self._clean_old_backups()
            else:
                logger.error("Backup failed")
        
        except Exception as e:
            logger.error(f"Error in scheduled backup: {e}", exc_info=True)
    
    def _clean_old_backups(self) -> None:
        """Clean old backup files."""
        try:
            backup_config = self.config.get("management", {}).get("backup", {})
            retention_days = backup_config.get("retention_days", 30)
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for backup_file in self.logs_dir.glob("metadata_backup_*.db"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file}")
        
        except Exception as e:
            logger.error(f"Error cleaning old backups: {e}")
    
    def _update_statistics(self) -> None:
        """Update agent statistics."""
        try:
            self.agent_stats["last_activity"] = datetime.now().isoformat()
            
            # Calculate uptime
            if self.agent_stats["start_time"]:
                start_time = datetime.fromisoformat(self.agent_stats["start_time"])
                uptime = datetime.now() - start_time
                self.agent_stats["uptime_seconds"] = uptime.total_seconds()
        
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and statistics.
        
        Returns:
            Dictionary with agent status
        """
        status = {
            "is_running": self.is_running,
            "agent_stats": self.agent_stats.copy(),
            "component_stats": {
                "collector": self.collector.get_collection_stats(),
                "processor": self.processor.get_processing_stats(),
                "validator": self.validator.get_validation_stats(),
                "manager": self.manager.get_storage_stats()
            },
            "learning_memory": {
                "successful_sources_count": len(self.learning_memory["successful_sources"]),
                "failed_sources_count": len(self.learning_memory["failed_sources"]),
                "quality_patterns_count": len(self.learning_memory["quality_patterns"]),
                "processing_preferences_count": len(self.learning_memory["processing_preferences"])
            },
            "last_operations": {
                "collection": self.last_collection_time.isoformat() if self.last_collection_time else None,
                "processing": self.last_processing_time.isoformat() if self.last_processing_time else None,
                "validation": self.last_validation_time.isoformat() if self.last_validation_time else None
            }
        }
        
        return status
    
    def manual_collection(self, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Manually trigger data collection.
        
        Args:
            sources: List of sources to collect from (all if None)
            
        Returns:
            Collection result
        """
        logger.info(f"Manual collection triggered for sources: {sources or 'all'}")
        
        try:
            # Force collection regardless of timing constraints
            original_last_time = self.last_collection_time
            self.last_collection_time = None
            
            # Perform collection
            self._autonomous_collection()
            
            # Restore original time if collection was successful
            if not self.last_collection_time:
                self.last_collection_time = original_last_time
            
            return {"success": True, "message": "Manual collection completed"}
        
        except Exception as e:
            logger.error(f"Error in manual collection: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def manual_processing(self, dataset_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Manually trigger data processing.
        
        Args:
            dataset_names: List of dataset names to process (all unprocessed if None)
            
        Returns:
            Processing result
        """
        logger.info(f"Manual processing triggered for datasets: {dataset_names or 'all unprocessed'}")
        
        try:
            # Force processing
            self._autonomous_processing()
            
            return {"success": True, "message": "Manual processing completed"}
        
        except Exception as e:
            logger.error(f"Error in manual processing: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def manual_validation(self, dataset_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Manually trigger data validation.
        
        Args:
            dataset_names: List of dataset names to validate (all unvalidated if None)
            
        Returns:
            Validation result
        """
        logger.info(f"Manual validation triggered for datasets: {dataset_names or 'all unvalidated'}")
        
        try:
            # Force validation
            self._autonomous_validation()
            
            return {"success": True, "message": "Manual validation completed"}
        
        except Exception as e:
            logger.error(f"Error in manual validation: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update agent configuration.
        
        Args:
            new_config: New configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Merge with existing config
            self.config = self._merge_configs(self.config, new_config)
            
            # Save to file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("Configuration updated successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error updating configuration: {e}", exc_info=True)
            return False
    
    def export_learning_memory(self, export_path: str) -> bool:
        """Export learning memory to file (production-ready).
        Args:
            export_path: Path to export file
        Returns:
            True if successful, False otherwise
        """
        try:
            exportable_memory = {
                "successful_sources": sorted(list(self.learning_memory["successful_sources"])),
                "failed_sources": sorted(list(self.learning_memory["failed_sources"])),
                "quality_patterns": self.learning_memory["quality_patterns"],
                "processing_preferences": self.learning_memory["processing_preferences"],
                "validation_insights": self.learning_memory["validation_insights"]
            }
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(exportable_memory, f, indent=2, ensure_ascii=False)
            logger.info(f"Learning memory exported to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting learning memory: {e}", exc_info=True)
            return False

    def import_learning_memory(self, import_path: str) -> bool:
        """Import learning memory from file (production-ready).
        Args:
            import_path: Path to import file
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(import_path):
                logger.error(f"Import path does not exist: {import_path}")
                return False
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_memory = json.load(f)
            self.learning_memory["successful_sources"] = set(imported_memory.get("successful_sources", []))
            self.learning_memory["failed_sources"] = set(imported_memory.get("failed_sources", []))
            self.learning_memory["quality_patterns"] = imported_memory.get("quality_patterns", {})
            self.learning_memory["processing_preferences"] = imported_memory.get("processing_preferences", {})
            self.learning_memory["validation_insights"] = imported_memory.get("validation_insights", {})
            logger.info(f"Learning memory imported from {import_path}")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error importing learning memory: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error importing learning memory: {e}", exc_info=True)
            return False

"""Data management module for the EGen platform.

This module provides components for data management,
version control, metadata tracking, and storage optimization.
"""

import json
import logging
import os
import shutil
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("Pandas not available. Install with: pip install pandas")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available. Install with: pip install numpy")

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    logging.warning("GitPython not available. Install with: pip install GitPython")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DataManager:
    """Data manager for the EGen platform.
    
    This class provides methods for data management,
    version control, metadata tracking, and storage optimization.
    """

    def __init__(
        self,
        data_dir: str = "./data_repository",
        metadata_db: str = "./metadata.db",
        enable_versioning: bool = True,
        enable_compression: bool = True,
        max_versions: int = 10,
        storage_limit_gb: float = 100.0,
        auto_cleanup: bool = True
    ):
        """Initialize the data manager.
        
        Args:
            data_dir: Directory for data storage
            metadata_db: Path to metadata database
            enable_versioning: Whether to enable version control
            enable_compression: Whether to enable data compression
            max_versions: Maximum number of versions to keep
            storage_limit_gb: Storage limit in GB
            auto_cleanup: Whether to enable automatic cleanup
        """
        self.data_dir = Path(data_dir)
        self.metadata_db = metadata_db
        self.enable_versioning = enable_versioning
        self.enable_compression = enable_compression
        self.max_versions = max_versions
        self.storage_limit_gb = storage_limit_gb
        self.auto_cleanup = auto_cleanup
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir = self.data_dir / "versions"
        self.metadata_dir = self.data_dir / "metadata"
        self.temp_dir = self.data_dir / "temp"
        
        for dir_path in [self.versions_dir, self.metadata_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata database
        self._init_metadata_db()
        
        # Initialize Git repository if versioning enabled
        self.git_repo = None
        if self.enable_versioning and GIT_AVAILABLE:
            self._init_git_repo()
        
        # Management statistics
        self.management_stats = {
            "datasets_managed": 0,
            "total_storage_used_gb": 0.0,
            "versions_created": 0,
            "cleanups_performed": 0,
            "last_cleanup": None,
            "last_backup": None
        }
        
        # Update storage statistics
        self._update_storage_stats()
    
    def _init_metadata_db(self) -> None:
        """Initialize the metadata database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            # Create datasets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    source TEXT,
                    format TEXT,
                    size_bytes INTEGER,
                    records_count INTEGER,
                    columns_count INTEGER,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    checksum TEXT,
                    tags TEXT,
                    metadata_json TEXT
                )
            """)
            
            # Create versions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    size_bytes INTEGER,
                    checksum TEXT,
                    created_at TIMESTAMP,
                    commit_hash TEXT,
                    changes_description TEXT,
                    FOREIGN KEY (dataset_name) REFERENCES datasets (name)
                )
            """)
            
            # Create storage_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS storage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    total_size_gb REAL,
                    datasets_count INTEGER,
                    versions_count INTEGER,
                    cleanup_triggered BOOLEAN
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Metadata database initialized")
        
        except Exception as e:
            logger.error(f"Error initializing metadata database: {e}", exc_info=True)
    
    def _init_git_repo(self) -> None:
        """Initialize Git repository for version control."""
        try:
            repo_path = self.data_dir / ".git"
            
            if repo_path.exists():
                self.git_repo = git.Repo(self.data_dir)
                logger.info("Existing Git repository found")
            else:
                self.git_repo = git.Repo.init(self.data_dir)
                
                # Create .gitignore
                gitignore_path = self.data_dir / ".gitignore"
                with open(gitignore_path, 'w') as f:
                    f.write("temp/\n*.tmp\n*.log\n__pycache__/\n")
                
                # Initial commit
                self.git_repo.index.add([".gitignore"])
                self.git_repo.index.commit("Initial commit")
                
                logger.info("Git repository initialized")
        
        except Exception as e:
            logger.warning(f"Failed to initialize Git repository: {e}")
            self.git_repo = None
    
    def store_dataset(
        self,
        data: Union[List[Dict], pd.DataFrame, str],
        dataset_name: str,
        description: str = "",
        source: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """Store a dataset with metadata and versioning.
        
        Args:
            data: Dataset to store (list of dicts, DataFrame, or file path)
            dataset_name: Name of the dataset
            description: Description of the dataset
            source: Source of the dataset
            tags: List of tags for the dataset
            metadata: Additional metadata
            force_update: Whether to force update existing dataset
            
        Returns:
            Storage result with metadata
        """
        logger.info(f"Storing dataset: {dataset_name}")
        
        storage_result = {
            "dataset_name": dataset_name,
            "storage_timestamp": datetime.now().isoformat(),
            "success": False,
            "version": 1,
            "file_path": None,
            "size_bytes": 0,
            "checksum": None,
            "metadata": {}
        }
        
        try:
            # Load data if path provided
            if isinstance(data, str):
                data = self._load_data(data)
            
            # Check if dataset already exists
            existing_dataset = self._get_dataset_metadata(dataset_name)
            if existing_dataset and not force_update:
                logger.warning(f"Dataset {dataset_name} already exists. Use force_update=True to overwrite.")
                storage_result["error"] = "Dataset already exists"
                return storage_result
            
            # Determine file format and path
            file_format = "json" if isinstance(data, list) else "csv"
            if existing_dataset:
                storage_result["version"] = existing_dataset["version"] + 1
            
            filename = f"{dataset_name}_v{storage_result['version']}.{file_format}"
            file_path = self.data_dir / filename
            
            # Save data to file
            if isinstance(data, list):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            elif PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False)
            else:
                raise ValueError("Unsupported data format")
            
            # Calculate file statistics
            file_size = file_path.stat().st_size
            file_checksum = self._calculate_checksum(file_path)
            
            # Get data statistics
            data_stats = self._get_data_statistics(data)
            
            # Prepare metadata
            full_metadata = {
                "description": description,
                "source": source,
                "tags": tags or [],
                "statistics": data_stats,
                "custom_metadata": metadata or {}
            }
            
            # Store metadata in database
            self._store_dataset_metadata(
                dataset_name=dataset_name,
                description=description,
                source=source,
                format=file_format,
                size_bytes=file_size,
                records_count=data_stats.get("records_count", 0),
                columns_count=data_stats.get("columns_count", 0),
                version=storage_result["version"],
                checksum=file_checksum,
                tags=tags,
                metadata=full_metadata
            )
            
            # Store version information
            if self.enable_versioning:
                self._store_version_metadata(
                    dataset_name=dataset_name,
                    version=storage_result["version"],
                    file_path=str(file_path),
                    size_bytes=file_size,
                    checksum=file_checksum,
                    changes_description=f"Version {storage_result['version']} update"
                )
                
                # Git commit if available
                if self.git_repo:
                    self._git_commit(file_path, f"Add {dataset_name} version {storage_result['version']}")
            
            # Compression if enabled
            if self.enable_compression:
                compressed_path = self._compress_file(file_path)
                if compressed_path:
                    file_path.unlink()  # Remove original
                    file_path = compressed_path
            
            # Update storage result
            storage_result.update({
                "success": True,
                "file_path": str(file_path),
                "size_bytes": file_size,
                "checksum": file_checksum,
                "metadata": full_metadata
            })
            
            # Update statistics
            self.management_stats["datasets_managed"] += 1
            if self.enable_versioning:
                self.management_stats["versions_created"] += 1
            
            # Auto cleanup if needed
            if self.auto_cleanup:
                self._auto_cleanup()
            
            logger.info(f"Dataset {dataset_name} stored successfully (version {storage_result['version']})")
        
        except Exception as e:
            logger.error(f"Error storing dataset {dataset_name}: {e}", exc_info=True)
            storage_result["error"] = str(e)
        
        return storage_result
    
    def retrieve_dataset(
        self,
        dataset_name: str,
        version: Optional[int] = None,
        decompress: bool = True
    ) -> Dict[str, Any]:
        """Retrieve a dataset by name and version.
        
        Args:
            dataset_name: Name of the dataset
            version: Specific version to retrieve (latest if None)
            decompress: Whether to decompress if compressed
            
        Returns:
            Retrieved dataset with metadata
        """
        logger.info(f"Retrieving dataset: {dataset_name} (version: {version or 'latest'})")
        
        retrieval_result = {
            "dataset_name": dataset_name,
            "retrieval_timestamp": datetime.now().isoformat(),
            "success": False,
            "data": None,
            "metadata": {},
            "version": None
        }
        
        try:
            # Get dataset metadata
            dataset_metadata = self._get_dataset_metadata(dataset_name)
            if not dataset_metadata:
                retrieval_result["error"] = "Dataset not found"
                return retrieval_result
            
            # Determine version to retrieve
            target_version = version or dataset_metadata["version"]
            
            # Get version metadata
            version_metadata = self._get_version_metadata(dataset_name, target_version)
            if not version_metadata:
                retrieval_result["error"] = f"Version {target_version} not found"
                return retrieval_result
            
            # Get file path
            file_path = Path(version_metadata["file_path"])
            
            # Check if file is compressed
            if file_path.suffix == '.gz' and decompress:
                file_path = self._decompress_file(file_path)
            
            # Load data
            if not file_path.exists():
                retrieval_result["error"] = "Data file not found"
                return retrieval_result
            
            data = self._load_data(str(file_path))
            
            # Update retrieval result
            retrieval_result.update({
                "success": True,
                "data": data,
                "metadata": json.loads(dataset_metadata.get("metadata_json", "{}")),
                "version": target_version
            })
            
            logger.info(f"Dataset {dataset_name} retrieved successfully (version {target_version})")
        
        except Exception as e:
            logger.error(f"Error retrieving dataset {dataset_name}: {e}", exc_info=True)
            retrieval_result["error"] = str(e)
        
        return retrieval_result
    
    def list_datasets(
        self,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List all managed datasets.
        
        Args:
            tags: Filter by tags
            source: Filter by source
            limit: Maximum number of results
            
        Returns:
            List of dataset metadata
        """
        try:
            conn = sqlite3.connect(self.metadata_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM datasets WHERE 1=1"
            params = []
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            if tags:
                for tag in tags:
                    query += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            
            query += " ORDER BY updated_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            datasets = []
            for row in rows:
                dataset = dict(row)
                # Parse JSON fields
                if dataset["tags"]:
                    dataset["tags"] = json.loads(dataset["tags"])
                if dataset["metadata_json"]:
                    dataset["metadata"] = json.loads(dataset["metadata_json"])
                    del dataset["metadata_json"]
                datasets.append(dataset)
            
            conn.close()
            return datasets
        
        except Exception as e:
            logger.error(f"Error listing datasets: {e}", exc_info=True)
            return []
    
    def delete_dataset(
        self,
        dataset_name: str,
        version: Optional[int] = None,
        delete_all_versions: bool = False
    ) -> Dict[str, Any]:
        """Delete a dataset or specific version.
        
        Args:
            dataset_name: Name of the dataset
            version: Specific version to delete (all if None)
            delete_all_versions: Whether to delete all versions
            
        Returns:
            Deletion result
        """
        logger.info(f"Deleting dataset: {dataset_name} (version: {version or 'all'})")
        
        deletion_result = {
            "dataset_name": dataset_name,
            "deletion_timestamp": datetime.now().isoformat(),
            "success": False,
            "deleted_versions": [],
            "freed_space_bytes": 0
        }
        
        try:
            if delete_all_versions or version is None:
                # Delete all versions
                versions = self._get_all_versions(dataset_name)
                for version_info in versions:
                    file_path = Path(version_info["file_path"])
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deletion_result["freed_space_bytes"] += file_size
                        deletion_result["deleted_versions"].append(version_info["version"])
                
                # Delete from database
                self._delete_dataset_metadata(dataset_name)
                self._delete_all_version_metadata(dataset_name)
            
            else:
                # Delete specific version
                version_metadata = self._get_version_metadata(dataset_name, version)
                if version_metadata:
                    file_path = Path(version_metadata["file_path"])
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deletion_result["freed_space_bytes"] = file_size
                        deletion_result["deleted_versions"].append(version)
                    
                    # Delete version metadata
                    self._delete_version_metadata(dataset_name, version)
                    
                    # Update dataset version if this was the latest
                    remaining_versions = self._get_all_versions(dataset_name)
                    if remaining_versions:
                        latest_version = max(v["version"] for v in remaining_versions)
                        self._update_dataset_version(dataset_name, latest_version)
                    else:
                        # No versions left, delete dataset
                        self._delete_dataset_metadata(dataset_name)
            
            deletion_result["success"] = True
            
            # Git commit if available
            if self.git_repo:
                self._git_commit(None, f"Delete {dataset_name} version(s): {deletion_result['deleted_versions']}")
            
            logger.info(f"Dataset {dataset_name} deleted successfully")
        
        except Exception as e:
            logger.error(f"Error deleting dataset {dataset_name}: {e}", exc_info=True)
            deletion_result["error"] = str(e)
        
        return deletion_result
    
    def _load_data(self, file_path: str) -> Union[List[Dict], pd.DataFrame]:
        """Load data from file.
        
        Args:
            file_path: Path to data file
            
        Returns:
            Loaded data
        """
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        # Handle compressed files
        if file_ext == '.gz':
            file_ext = file_path.stem.split('.')[-1]
        
        try:
            if file_ext == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif file_ext in ['csv', 'tsv'] and PANDAS_AVAILABLE:
                delimiter = '\t' if file_ext == 'tsv' else ','
                return pd.read_csv(file_path, delimiter=delimiter)
            
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            raise
    
    def _get_data_statistics(self, data: Union[List[Dict], pd.DataFrame]) -> Dict[str, Any]:
        """Get statistics about the data.
        
        Args:
            data: Data to analyze
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            "records_count": 0,
            "columns_count": 0,
            "data_types": {},
            "memory_usage_bytes": 0
        }
        
        try:
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                stats["records_count"] = len(data)
                stats["columns_count"] = len(data.columns)
                stats["data_types"] = {col: str(dtype) for col, dtype in data.dtypes.items()}
                stats["memory_usage_bytes"] = data.memory_usage(deep=True).sum()
            
            elif isinstance(data, list):
                stats["records_count"] = len(data)
                if data and isinstance(data[0], dict):
                    stats["columns_count"] = len(data[0])
                    # Estimate memory usage
                    sample_size = len(str(data[0]).encode('utf-8'))
                    stats["memory_usage_bytes"] = sample_size * len(data)
        
        except Exception as e:
            logger.warning(f"Error calculating data statistics: {e}")
        
        return stats
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 checksum string
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Error calculating checksum: {e}")
            return ""
    
    def _compress_file(self, file_path: Path) -> Optional[Path]:
        """Compress a file using gzip.
        
        Args:
            file_path: Path to the file to compress
            
        Returns:
            Path to compressed file or None if failed
        """
        try:
            import gzip
            
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"File compressed: {file_path} -> {compressed_path}")
            return compressed_path
        
        except Exception as e:
            logger.warning(f"Error compressing file {file_path}: {e}")
            return None
    
    def _decompress_file(self, file_path: Path) -> Path:
        """Decompress a gzip file.
        
        Args:
            file_path: Path to the compressed file
            
        Returns:
            Path to decompressed file
        """
        try:
            import gzip
            
            decompressed_path = self.temp_dir / file_path.stem
            
            with gzip.open(file_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return decompressed_path
        
        except Exception as e:
            logger.error(f"Error decompressing file {file_path}: {e}")
            raise
    
    def _store_dataset_metadata(self, **kwargs) -> None:
        """Store dataset metadata in database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            # Check if dataset exists
            cursor.execute("SELECT id FROM datasets WHERE name = ?", (kwargs["dataset_name"],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing dataset
                cursor.execute("""
                    UPDATE datasets SET
                        description = ?, source = ?, format = ?, size_bytes = ?,
                        records_count = ?, columns_count = ?, updated_at = ?,
                        version = ?, checksum = ?, tags = ?, metadata_json = ?
                    WHERE name = ?
                """, (
                    kwargs["description"], kwargs["source"], kwargs["format"],
                    kwargs["size_bytes"], kwargs["records_count"], kwargs["columns_count"],
                    datetime.now(), kwargs["version"], kwargs["checksum"],
                    json.dumps(kwargs["tags"]) if kwargs["tags"] else None,
                    json.dumps(kwargs["metadata"]) if kwargs["metadata"] else None,
                    kwargs["dataset_name"]
                ))
            else:
                # Insert new dataset
                cursor.execute("""
                    INSERT INTO datasets (
                        name, description, source, format, size_bytes,
                        records_count, columns_count, created_at, updated_at,
                        version, checksum, tags, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kwargs["dataset_name"], kwargs["description"], kwargs["source"],
                    kwargs["format"], kwargs["size_bytes"], kwargs["records_count"],
                    kwargs["columns_count"], datetime.now(), datetime.now(),
                    kwargs["version"], kwargs["checksum"],
                    json.dumps(kwargs["tags"]) if kwargs["tags"] else None,
                    json.dumps(kwargs["metadata"]) if kwargs["metadata"] else None
                ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error storing dataset metadata: {e}", exc_info=True)
    
    def _store_version_metadata(self, **kwargs) -> None:
        """Store version metadata in database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO versions (
                    dataset_name, version, file_path, size_bytes,
                    checksum, created_at, commit_hash, changes_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs["dataset_name"], kwargs["version"], kwargs["file_path"],
                kwargs["size_bytes"], kwargs["checksum"], datetime.now(),
                kwargs.get("commit_hash"), kwargs.get("changes_description")
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error storing version metadata: {e}", exc_info=True)
    
    def _get_dataset_metadata(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """Get dataset metadata from database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM datasets WHERE name = ?", (dataset_name,))
            row = cursor.fetchone()
            
            conn.close()
            
            return dict(row) if row else None
        
        except Exception as e:
            logger.error(f"Error getting dataset metadata: {e}", exc_info=True)
            return None
    
    def _get_version_metadata(self, dataset_name: str, version: int) -> Optional[Dict[str, Any]]:
        """Get version metadata from database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM versions WHERE dataset_name = ? AND version = ?",
                (dataset_name, version)
            )
            row = cursor.fetchone()
            
            conn.close()
            
            return dict(row) if row else None
        
        except Exception as e:
            logger.error(f"Error getting version metadata: {e}", exc_info=True)
            return None
    
    def _get_all_versions(self, dataset_name: str) -> List[Dict[str, Any]]:
        """Get all versions for a dataset."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM versions WHERE dataset_name = ? ORDER BY version DESC",
                (dataset_name,)
            )
            rows = cursor.fetchall()
            
            conn.close()
            
            return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f"Error getting all versions: {e}", exc_info=True)
            return []
    
    def _delete_dataset_metadata(self, dataset_name: str) -> None:
        """Delete dataset metadata from database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM datasets WHERE name = ?", (dataset_name,))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error deleting dataset metadata: {e}", exc_info=True)
    
    def _delete_version_metadata(self, dataset_name: str, version: int) -> None:
        """Delete version metadata from database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM versions WHERE dataset_name = ? AND version = ?",
                (dataset_name, version)
            )
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error deleting version metadata: {e}", exc_info=True)
    
    def _delete_all_version_metadata(self, dataset_name: str) -> None:
        """Delete all version metadata for a dataset."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM versions WHERE dataset_name = ?", (dataset_name,))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error deleting all version metadata: {e}", exc_info=True)
    
    def _update_dataset_version(self, dataset_name: str, version: int) -> None:
        """Update dataset version in database."""
        try:
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE datasets SET version = ?, updated_at = ? WHERE name = ?",
                (version, datetime.now(), dataset_name)
            )
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error updating dataset version: {e}", exc_info=True)
    
    def _git_commit(self, file_path: Optional[Path], message: str) -> None:
        """Create a Git commit."""
        try:
            if not self.git_repo:
                return
            
            if file_path:
                self.git_repo.index.add([str(file_path.relative_to(self.data_dir))])
            
            self.git_repo.index.commit(message)
            
        except Exception as e:
            logger.warning(f"Error creating Git commit: {e}")
    
    def _update_storage_stats(self) -> None:
        """Update storage statistics."""
        try:
            total_size = 0
            for file_path in self.data_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            total_size_gb = total_size / (1024 ** 3)
            self.management_stats["total_storage_used_gb"] = total_size_gb
            
            # Store in database
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            datasets_count = cursor.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
            versions_count = cursor.execute("SELECT COUNT(*) FROM versions").fetchone()[0]
            
            cursor.execute("""
                INSERT INTO storage_stats (
                    timestamp, total_size_gb, datasets_count, versions_count, cleanup_triggered
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now(), total_size_gb, datasets_count, versions_count,
                total_size_gb > self.storage_limit_gb
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error updating storage stats: {e}", exc_info=True)
    
    def _auto_cleanup(self) -> None:
        """Perform automatic cleanup if storage limit exceeded."""
        try:
            self._update_storage_stats()
            
            if self.management_stats["total_storage_used_gb"] > self.storage_limit_gb:
                logger.info("Storage limit exceeded, performing cleanup")
                
                # Get datasets sorted by last access (oldest first)
                datasets = self.list_datasets()
                datasets.sort(key=lambda x: x["updated_at"])
                
                freed_space = 0
                target_space = self.storage_limit_gb * 0.8  # Clean to 80% of limit
                
                for dataset in datasets:
                    if self.management_stats["total_storage_used_gb"] <= target_space:
                        break
                    
                    # Remove old versions (keep only latest)
                    versions = self._get_all_versions(dataset["name"])
                    if len(versions) > 1:
                        for version_info in versions[1:]:  # Skip latest (first)
                            result = self.delete_dataset(
                                dataset["name"], 
                                version_info["version"]
                            )
                            if result["success"]:
                                freed_space += result["freed_space_bytes"]
                
                self.management_stats["cleanups_performed"] += 1
                self.management_stats["last_cleanup"] = datetime.now().isoformat()
                
                logger.info(f"Cleanup completed, freed {freed_space / (1024**3):.2f} GB")
        
        except Exception as e:
            logger.error(f"Error during auto cleanup: {e}", exc_info=True)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        self._update_storage_stats()
        return self.management_stats.copy()
    
    def backup_metadata(self, backup_path: str) -> bool:
        """Backup metadata database.
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(self.metadata_db, backup_path)
            self.management_stats["last_backup"] = datetime.now().isoformat()
            logger.info(f"Metadata backed up to {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error backing up metadata: {e}", exc_info=True)
            return False
    
    def restore_metadata(self, backup_path: str) -> bool:
        """Restore metadata database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(backup_path, self.metadata_db)
            logger.info(f"Metadata restored from {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error restoring metadata: {e}", exc_info=True)
            return False
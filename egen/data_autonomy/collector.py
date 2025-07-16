"""Data collection module for the EGen platform.

This module provides components for collecting data from various sources
including Hugging Face Hub, web crawling, and local datasets.
"""

import json
import logging
import os
import re
import requests
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

try:
    from datasets import load_dataset, list_datasets
    from huggingface_hub import HfApi, list_datasets as hf_list_datasets
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logging.warning("Hugging Face datasets not available. Install with: pip install datasets")

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    logging.warning("Web scraping dependencies not available. Install with: pip install beautifulsoup4")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DataCollector:
    """Data collector for the EGen platform.
    
    This class provides methods for collecting data from various sources
    including Hugging Face Hub, web crawling, and local datasets.
    """

    def __init__(
        self,
        cache_dir: str = "./data_cache",
        max_dataset_size: int = 1000000,  # 1M samples
        supported_formats: Optional[List[str]] = None,
        rate_limit_delay: float = 1.0,  # seconds between requests
        user_agent: str = "EGen-DataCollector/1.0",
    ):
        """Initialize the data collector.
        
        Args:
            cache_dir: Directory to cache downloaded datasets
            max_dataset_size: Maximum number of samples per dataset
            supported_formats: List of supported data formats
            rate_limit_delay: Delay between web requests
            user_agent: User agent string for web requests
        """
        self.cache_dir = cache_dir
        self.max_dataset_size = max_dataset_size
        self.supported_formats = supported_formats or [
            "json", "jsonl", "csv", "tsv", "txt", "parquet"
        ]
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize Hugging Face API if available
        self.hf_api = HfApi() if HF_AVAILABLE else None
        
        # Collection statistics
        self.collection_stats = {
            "datasets_collected": 0,
            "total_samples": 0,
            "sources": {},
            "last_collection": None
        }
    
    def search_huggingface_datasets(
        self,
        query: str,
        task: Optional[str] = None,
        language: Optional[str] = None,
        size_category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for datasets on Hugging Face Hub.
        
        Args:
            query: Search query string
            task: Task type (e.g., 'text-classification', 'translation')
            language: Language code (e.g., 'en', 'es')
            size_category: Size category (e.g., 'n<1K', '1K<n<10K')
            limit: Maximum number of results
            
        Returns:
            List of dataset information dictionaries
        """
        if not HF_AVAILABLE:
            logger.error("Hugging Face datasets not available")
            return []
        
        try:
            # Search datasets using HF API
            datasets = list(hf_list_datasets(
                search=query,
                task=task,
                language=language,
                size_category=size_category,
                limit=limit
            ))
            
            results = []
            for dataset in datasets:
                dataset_info = {
                    "id": dataset.id,
                    "name": dataset.id.split("/")[-1],
                    "author": dataset.author,
                    "description": getattr(dataset, 'description', ''),
                    "tags": getattr(dataset, 'tags', []),
                    "downloads": getattr(dataset, 'downloads', 0),
                    "likes": getattr(dataset, 'likes', 0),
                    "size_category": getattr(dataset, 'size_category', 'unknown'),
                    "task_categories": getattr(dataset, 'task_categories', []),
                    "language": getattr(dataset, 'language', []),
                    "source": "huggingface",
                    "url": f"https://huggingface.co/datasets/{dataset.id}"
                }
                results.append(dataset_info)
            
            logger.info(f"Found {len(results)} datasets on Hugging Face Hub")
            return results
        
        except Exception as e:
            logger.error(f"Error searching Hugging Face datasets: {e}", exc_info=True)
            return []
    
    def download_huggingface_dataset(
        self,
        dataset_id: str,
        config_name: Optional[str] = None,
        split: Optional[str] = None,
        streaming: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Download a dataset from Hugging Face Hub.
        
        Args:
            dataset_id: Dataset identifier
            config_name: Configuration name
            split: Dataset split (train, validation, test)
            streaming: Whether to use streaming mode
            
        Returns:
            Dataset information dictionary or None if failed
        """
        if not HF_AVAILABLE:
            logger.error("Hugging Face datasets not available")
            return None
        
        try:
            # Load dataset
            dataset = load_dataset(
                dataset_id,
                name=config_name,
                split=split,
                streaming=streaming,
                cache_dir=self.cache_dir
            )
            
            # Get dataset info
            dataset_info = {
                "id": dataset_id,
                "config_name": config_name,
                "split": split,
                "num_rows": len(dataset) if not streaming else "unknown",
                "features": list(dataset.features.keys()) if hasattr(dataset, 'features') else [],
                "cache_files": dataset.cache_files if hasattr(dataset, 'cache_files') else [],
                "source": "huggingface",
                "downloaded_at": datetime.now().isoformat(),
                "streaming": streaming
            }
            
            # Update statistics
            self.collection_stats["datasets_collected"] += 1
            if not streaming:
                self.collection_stats["total_samples"] += len(dataset)
            self.collection_stats["sources"]["huggingface"] = \
                self.collection_stats["sources"].get("huggingface", 0) + 1
            self.collection_stats["last_collection"] = datetime.now().isoformat()
            
            logger.info(f"Downloaded dataset {dataset_id} with {dataset_info['num_rows']} rows")
            return dataset_info
        
        except Exception as e:
            logger.error(f"Error downloading dataset {dataset_id}: {e}", exc_info=True)
            return None
    
    def crawl_web_datasets(
        self,
        urls: List[str],
        file_patterns: Optional[List[str]] = None,
        max_depth: int = 2,
        max_files: int = 100
    ) -> List[Dict[str, Any]]:
        """Crawl websites for dataset files.
        
        Args:
            urls: List of URLs to crawl
            file_patterns: List of file patterns to match
            max_depth: Maximum crawling depth
            max_files: Maximum number of files to collect
            
        Returns:
            List of discovered dataset file information
        """
        if not WEB_SCRAPING_AVAILABLE:
            logger.error("Web scraping dependencies not available")
            return []
        
        file_patterns = file_patterns or [
            r'.*\.(json|jsonl|csv|tsv|txt|parquet)$',
            r'.*dataset.*\.(zip|tar\.gz|tar)$',
            r'.*data.*\.(zip|tar\.gz|tar)$'
        ]
        
        discovered_files = []
        visited_urls = set()
        
        for url in urls:
            try:
                files = self._crawl_url(
                    url, file_patterns, max_depth, max_files - len(discovered_files), visited_urls
                )
                discovered_files.extend(files)
                
                if len(discovered_files) >= max_files:
                    break
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
            
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}", exc_info=True)
                continue
        
        logger.info(f"Discovered {len(discovered_files)} dataset files")
        return discovered_files
    
    def _crawl_url(
        self,
        url: str,
        file_patterns: List[str],
        max_depth: int,
        max_files: int,
        visited_urls: set,
        current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """Recursively crawl a URL for dataset files.
        
        Args:
            url: URL to crawl
            file_patterns: File patterns to match
            max_depth: Maximum crawling depth
            max_files: Maximum files to collect
            visited_urls: Set of already visited URLs
            current_depth: Current crawling depth
            
        Returns:
            List of discovered files
        """
        if current_depth > max_depth or url in visited_urls or len(visited_urls) >= max_files:
            return []
        
        visited_urls.add(url)
        discovered_files = []
        
        try:
            # Make request with rate limiting
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Check if link matches file patterns
                for pattern in file_patterns:
                    if re.match(pattern, href, re.IGNORECASE):
                        file_info = {
                            "url": absolute_url,
                            "filename": os.path.basename(urlparse(absolute_url).path),
                            "source_url": url,
                            "discovered_at": datetime.now().isoformat(),
                            "source": "web_crawl",
                            "file_type": self._get_file_type(href)
                        }
                        discovered_files.append(file_info)
                        break
                
                # Recursively crawl subdirectories
                if (current_depth < max_depth and 
                    self._is_valid_crawl_url(absolute_url) and
                    len(discovered_files) < max_files):
                    
                    sub_files = self._crawl_url(
                        absolute_url, file_patterns, max_depth, 
                        max_files - len(discovered_files), visited_urls, current_depth + 1
                    )
                    discovered_files.extend(sub_files)
        
        except Exception as e:
            logger.debug(f"Error crawling {url}: {e}")
        
        return discovered_files
    
    def _is_valid_crawl_url(self, url: str) -> bool:
        """Check if URL is valid for crawling.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is valid for crawling
        """
        try:
            parsed = urlparse(url)
            
            # Skip non-HTTP URLs
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Skip common non-dataset URLs
            skip_patterns = [
                r'.*\.(js|css|png|jpg|jpeg|gif|svg|ico)$',
                r'.*/login.*',
                r'.*/logout.*',
                r'.*/admin.*',
                r'.*\?.*page=.*',
                r'.*#.*'
            ]
            
            for pattern in skip_patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    return False
            
            return True
        
        except Exception:
            return False
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from filename.
        
        Args:
            filename: Filename to analyze
            
        Returns:
            File type string
        """
        ext = os.path.splitext(filename)[1].lower()
        
        type_mapping = {
            '.json': 'json',
            '.jsonl': 'jsonl',
            '.csv': 'csv',
            '.tsv': 'tsv',
            '.txt': 'text',
            '.parquet': 'parquet',
            '.zip': 'archive',
            '.tar': 'archive',
            '.gz': 'archive'
        }
        
        return type_mapping.get(ext, 'unknown')
    
    def scan_local_datasets(
        self,
        directories: List[str],
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """Scan local directories for dataset files.
        
        Args:
            directories: List of directories to scan
            recursive: Whether to scan recursively
            
        Returns:
            List of discovered local dataset files
        """
        discovered_files = []
        
        for directory in directories:
            if not os.path.exists(directory):
                logger.warning(f"Directory does not exist: {directory}")
                continue
            
            try:
                if recursive:
                    for root, _, files in os.walk(directory):
                        for file in files:
                            file_path = os.path.join(root, file)
                            file_info = self._analyze_local_file(file_path)
                            if file_info:
                                discovered_files.append(file_info)
                else:
                    for file in os.listdir(directory):
                        file_path = os.path.join(directory, file)
                        if os.path.isfile(file_path):
                            file_info = self._analyze_local_file(file_path)
                            if file_info:
                                discovered_files.append(file_info)
            
            except Exception as e:
                logger.error(f"Error scanning directory {directory}: {e}", exc_info=True)
        
        logger.info(f"Discovered {len(discovered_files)} local dataset files")
        return discovered_files
    
    def _analyze_local_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Analyze a local file to determine if it's a dataset.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File information dictionary or None if not a dataset
        """
        try:
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Check if file extension is supported
            if file_ext[1:] not in self.supported_formats:
                return None
            
            # Get file stats
            stat = os.stat(file_path)
            
            file_info = {
                "path": file_path,
                "filename": filename,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_type": self._get_file_type(filename),
                "source": "local",
                "discovered_at": datetime.now().isoformat()
            }
            
            # Try to get additional metadata for known formats
            if file_ext == '.json':
                file_info.update(self._analyze_json_file(file_path))
            elif file_ext in ['.csv', '.tsv']:
                file_info.update(self._analyze_csv_file(file_path))
            
            return file_info
        
        except Exception as e:
            logger.debug(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _analyze_json_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a JSON file for dataset characteristics.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Additional metadata dictionary
        """
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first few lines to determine structure
                first_line = f.readline().strip()
                
                if first_line.startswith('['):
                    # JSON array format
                    metadata['format'] = 'json_array'
                elif first_line.startswith('{'):
                    # Check if it's JSONL or single JSON object
                    second_line = f.readline().strip()
                    if second_line.startswith('{'):
                        metadata['format'] = 'jsonl'
                    else:
                        metadata['format'] = 'json_object'
                
                # Try to count lines for JSONL
                if metadata.get('format') == 'jsonl':
                    f.seek(0)
                    line_count = sum(1 for _ in f)
                    metadata['estimated_rows'] = line_count
        
        except Exception as e:
            logger.debug(f"Error analyzing JSON file {file_path}: {e}")
        
        return metadata
    
    def _analyze_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a CSV file for dataset characteristics.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Additional metadata dictionary
        """
        metadata = {}
        
        try:
            import csv
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                # Read header
                reader = csv.reader(f, delimiter=delimiter)
                header = next(reader, None)
                
                if header:
                    metadata['columns'] = header
                    metadata['num_columns'] = len(header)
                
                # Count rows (approximate)
                f.seek(0)
                row_count = sum(1 for _ in reader) - 1  # Subtract header
                metadata['estimated_rows'] = row_count
                metadata['delimiter'] = delimiter
        
        except Exception as e:
            logger.debug(f"Error analyzing CSV file {file_path}: {e}")
        
        return metadata
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get data collection statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        return self.collection_stats.copy()
    
    def save_collection_report(self, output_path: str) -> None:
        """Save a collection report to file.
        
        Args:
            output_path: Path to save the report
        """
        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "statistics": self.get_collection_stats(),
                "configuration": {
                    "cache_dir": self.cache_dir,
                    "max_dataset_size": self.max_dataset_size,
                    "supported_formats": self.supported_formats,
                    "rate_limit_delay": self.rate_limit_delay
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Collection report saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving collection report: {e}", exc_info=True)
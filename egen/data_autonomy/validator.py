"""Data validation module for the EGen platform.

This module provides components for validating data quality,
detecting bias, and ensuring data integrity.
"""

import json
import logging
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
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
    from textstat import flesch_reading_ease, flesch_kincaid_grade
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    logging.warning("Textstat not available. Install with: pip install textstat")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DataValidator:
    """Data validator for the EGen platform.
    
    This class provides methods for validating data quality,
    detecting bias, and ensuring data integrity.
    """

    def __init__(
        self,
        quality_thresholds: Optional[Dict[str, float]] = None,
        bias_detection_enabled: bool = True,
        deduplication_enabled: bool = True,
        text_analysis_enabled: bool = True,
        save_reports: bool = True,
        reports_dir: str = "./validation_reports"
    ):
        """Initialize the data validator.
        
        Args:
            quality_thresholds: Dictionary of quality metric thresholds
            bias_detection_enabled: Whether to enable bias detection
            deduplication_enabled: Whether to enable deduplication
            text_analysis_enabled: Whether to enable text analysis
            save_reports: Whether to save validation reports
            reports_dir: Directory to save validation reports
        """
        self.quality_thresholds = quality_thresholds or {
            "completeness": 0.95,  # 95% non-null values
            "uniqueness": 0.90,    # 90% unique values
            "consistency": 0.95,   # 95% consistent format
            "validity": 0.90,      # 90% valid values
            "readability_min": 30,  # Minimum readability score
            "readability_max": 100, # Maximum readability score
            "bias_score_max": 0.3   # Maximum bias score
        }
        
        self.bias_detection_enabled = bias_detection_enabled
        self.deduplication_enabled = deduplication_enabled
        self.text_analysis_enabled = text_analysis_enabled
        self.save_reports = save_reports
        self.reports_dir = reports_dir
        
        # Create reports directory
        if save_reports:
            os.makedirs(reports_dir, exist_ok=True)
        
        # Bias detection patterns
        self.bias_patterns = {
            "gender": [
                r'\b(he|she|his|her|him|man|woman|male|female|boy|girl|guy|lady)\b',
                r'\b(masculine|feminine|manly|womanly)\b'
            ],
            "race": [
                r'\b(white|black|asian|hispanic|latino|african|european|american)\b',
                r'\b(caucasian|negro|oriental)\b'
            ],
            "age": [
                r'\b(young|old|elderly|senior|teenager|adult|child|kid)\b',
                r'\b(millennial|boomer|gen[xz])\b'
            ],
            "religion": [
                r'\b(christian|muslim|jewish|hindu|buddhist|atheist|religious)\b',
                r'\b(catholic|protestant|islamic|judaism|hinduism|buddhism)\b'
            ],
            "socioeconomic": [
                r'\b(rich|poor|wealthy|broke|expensive|cheap|luxury|budget)\b',
                r'\b(upper|middle|lower|working)\s+class\b'
            ]
        }
        
        # Validation statistics
        self.validation_stats = {
            "datasets_validated": 0,
            "total_records": 0,
            "quality_issues_found": 0,
            "bias_issues_found": 0,
            "duplicates_found": 0,
            "last_validation": None
        }
    
    def validate_dataset(
        self,
        data: Union[List[Dict], pd.DataFrame, str],
        dataset_name: str = "unknown",
        text_columns: Optional[List[str]] = None,
        target_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a complete dataset.
        
        Args:
            data: Dataset to validate (list of dicts, DataFrame, or file path)
            dataset_name: Name of the dataset
            text_columns: List of text column names
            target_column: Name of target/label column
            
        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting validation of dataset: {dataset_name}")
        
        # Load data if path provided
        if isinstance(data, str):
            data = self._load_data(data)
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            if PANDAS_AVAILABLE:
                data = pd.DataFrame(data)
            else:
                logger.warning("Pandas not available, using basic validation")
        
        validation_report = {
            "dataset_name": dataset_name,
            "validation_timestamp": datetime.now().isoformat(),
            "data_shape": self._get_data_shape(data),
            "quality_metrics": {},
            "bias_analysis": {},
            "deduplication_analysis": {},
            "text_analysis": {},
            "issues": [],
            "recommendations": [],
            "overall_score": 0.0,
            "passed": False
        }
        
        try:
            # Basic quality metrics
            validation_report["quality_metrics"] = self._assess_data_quality(data)
            
            # Bias detection
            if self.bias_detection_enabled:
                validation_report["bias_analysis"] = self._detect_bias(
                    data, text_columns, target_column
                )
            
            # Deduplication analysis
            if self.deduplication_enabled:
                validation_report["deduplication_analysis"] = self._analyze_duplicates(data)
            
            # Text analysis
            if self.text_analysis_enabled and text_columns:
                validation_report["text_analysis"] = self._analyze_text_quality(
                    data, text_columns
                )
            
            # Generate issues and recommendations
            validation_report["issues"] = self._identify_issues(validation_report)
            validation_report["recommendations"] = self._generate_recommendations(
                validation_report
            )
            
            # Calculate overall score
            validation_report["overall_score"] = self._calculate_overall_score(
                validation_report
            )
            
            # Determine if validation passed
            validation_report["passed"] = (
                validation_report["overall_score"] >= 0.7 and
                len([issue for issue in validation_report["issues"] 
                     if issue["severity"] == "critical"]) == 0
            )
            
            # Update statistics
            self._update_validation_stats(validation_report)
            
            # Save report if enabled
            if self.save_reports:
                self._save_validation_report(validation_report)
            
            logger.info(
                f"Validation completed for {dataset_name}. "
                f"Score: {validation_report['overall_score']:.2f}, "
                f"Passed: {validation_report['passed']}"
            )
            
        except Exception as e:
            logger.error(f"Error during validation: {e}", exc_info=True)
            validation_report["error"] = str(e)
        
        return validation_report
    
    def _load_data(self, file_path: str) -> Union[List[Dict], pd.DataFrame]:
        """Load data from file.
        
        Args:
            file_path: Path to data file
            
        Returns:
            Loaded data
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif file_ext == '.jsonl':
                data = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        data.append(json.loads(line.strip()))
                return data
            
            elif file_ext in ['.csv', '.tsv'] and PANDAS_AVAILABLE:
                delimiter = '\t' if file_ext == '.tsv' else ','
                return pd.read_csv(file_path, delimiter=delimiter)
            
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            raise
    
    def _get_data_shape(self, data: Union[List[Dict], pd.DataFrame]) -> Tuple[int, int]:
        """Get the shape of the data.
        
        Args:
            data: Data to analyze
            
        Returns:
            Tuple of (rows, columns)
        """
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return data.shape
        elif isinstance(data, list) and data:
            return len(data), len(data[0]) if isinstance(data[0], dict) else 1
        else:
            return 0, 0
    
    def _assess_data_quality(self, data: Union[List[Dict], pd.DataFrame]) -> Dict[str, Any]:
        """Assess basic data quality metrics.
        
        Args:
            data: Data to assess
            
        Returns:
            Dictionary of quality metrics
        """
        quality_metrics = {
            "completeness": 0.0,
            "uniqueness": 0.0,
            "consistency": 0.0,
            "validity": 0.0,
            "column_metrics": {}
        }
        
        try:
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                # Completeness: percentage of non-null values
                quality_metrics["completeness"] = (
                    1 - data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
                )
                
                # Column-level metrics
                for column in data.columns:
                    col_metrics = {
                        "completeness": 1 - data[column].isnull().sum() / len(data),
                        "uniqueness": data[column].nunique() / len(data),
                        "data_type": str(data[column].dtype)
                    }
                    
                    # Type consistency
                    if data[column].dtype == 'object':
                        # Check string format consistency
                        non_null_values = data[column].dropna()
                        if len(non_null_values) > 0:
                            # Simple consistency check: similar string lengths
                            lengths = non_null_values.astype(str).str.len()
                            length_std = lengths.std() if len(lengths) > 1 else 0
                            col_metrics["consistency"] = max(0, 1 - length_std / lengths.mean())
                    else:
                        col_metrics["consistency"] = 1.0
                    
                    quality_metrics["column_metrics"][column] = col_metrics
                
                # Overall uniqueness
                total_unique = sum(data[col].nunique() for col in data.columns)
                total_values = data.shape[0] * data.shape[1]
                quality_metrics["uniqueness"] = total_unique / total_values if total_values > 0 else 0
                
                # Overall consistency (average of column consistencies)
                consistencies = [metrics["consistency"] for metrics in 
                               quality_metrics["column_metrics"].values()]
                quality_metrics["consistency"] = statistics.mean(consistencies) if consistencies else 0
                
                # Validity (placeholder - would need domain-specific rules)
                quality_metrics["validity"] = 0.9  # Assume 90% valid for now
            
            elif isinstance(data, list):
                # Basic analysis for list of dictionaries
                if not data:
                    return quality_metrics
                
                # Get all possible keys
                all_keys = set()
                for item in data:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                
                # Calculate completeness
                total_possible = len(data) * len(all_keys)
                total_present = sum(
                    len([k for k in item.keys() if item.get(k) is not None])
                    for item in data if isinstance(item, dict)
                )
                quality_metrics["completeness"] = total_present / total_possible if total_possible > 0 else 0
                
                # Basic uniqueness (count unique items)
                unique_items = len(set(str(item) for item in data))
                quality_metrics["uniqueness"] = unique_items / len(data) if data else 0
                
                # Consistency (all items have similar structure)
                if all_keys:
                    key_counts = Counter()
                    for item in data:
                        if isinstance(item, dict):
                            key_counts.update(item.keys())
                    
                    # Consistency based on key frequency
                    expected_count = len(data)
                    consistency_scores = [count / expected_count for count in key_counts.values()]
                    quality_metrics["consistency"] = statistics.mean(consistency_scores) if consistency_scores else 0
                
                quality_metrics["validity"] = 0.9  # Assume 90% valid
        
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}", exc_info=True)
        
        return quality_metrics
    
    def _detect_bias(
        self,
        data: Union[List[Dict], pd.DataFrame],
        text_columns: Optional[List[str]] = None,
        target_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect potential bias in the dataset.
        
        Args:
            data: Data to analyze
            text_columns: List of text column names
            target_column: Name of target/label column
            
        Returns:
            Dictionary of bias analysis results
        """
        bias_analysis = {
            "bias_score": 0.0,
            "bias_categories": {},
            "target_distribution": {},
            "text_bias": {},
            "recommendations": []
        }
        
        try:
            # Analyze target distribution if available
            if target_column:
                bias_analysis["target_distribution"] = self._analyze_target_distribution(
                    data, target_column
                )
            
            # Analyze text bias if text columns provided
            if text_columns:
                bias_analysis["text_bias"] = self._analyze_text_bias(data, text_columns)
            
            # Calculate overall bias score
            bias_scores = []
            
            # Target distribution bias
            if bias_analysis["target_distribution"].get("imbalance_ratio"):
                imbalance = bias_analysis["target_distribution"]["imbalance_ratio"]
                bias_scores.append(min(imbalance / 10, 1.0))  # Normalize to 0-1
            
            # Text bias
            for category, score in bias_analysis["text_bias"].items():
                if isinstance(score, dict) and "bias_score" in score:
                    bias_scores.append(score["bias_score"])
            
            bias_analysis["bias_score"] = statistics.mean(bias_scores) if bias_scores else 0.0
            
            # Generate recommendations
            if bias_analysis["bias_score"] > self.quality_thresholds["bias_score_max"]:
                bias_analysis["recommendations"].append(
                    "High bias detected. Consider data augmentation or rebalancing."
                )
        
        except Exception as e:
            logger.error(f"Error detecting bias: {e}", exc_info=True)
        
        return bias_analysis
    
    def _analyze_target_distribution(
        self,
        data: Union[List[Dict], pd.DataFrame],
        target_column: str
    ) -> Dict[str, Any]:
        """Analyze the distribution of target labels.
        
        Args:
            data: Data to analyze
            target_column: Name of target column
            
        Returns:
            Target distribution analysis
        """
        distribution_analysis = {
            "class_counts": {},
            "class_proportions": {},
            "imbalance_ratio": 0.0,
            "is_balanced": False
        }
        
        try:
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                if target_column in data.columns:
                    value_counts = data[target_column].value_counts()
                    distribution_analysis["class_counts"] = value_counts.to_dict()
                    
                    total = value_counts.sum()
                    distribution_analysis["class_proportions"] = {
                        k: v / total for k, v in value_counts.items()
                    }
                    
                    # Calculate imbalance ratio (max/min class ratio)
                    if len(value_counts) > 1:
                        max_count = value_counts.max()
                        min_count = value_counts.min()
                        distribution_analysis["imbalance_ratio"] = max_count / min_count
                        distribution_analysis["is_balanced"] = distribution_analysis["imbalance_ratio"] <= 2.0
            
            elif isinstance(data, list):
                # Analyze list of dictionaries
                target_values = []
                for item in data:
                    if isinstance(item, dict) and target_column in item:
                        target_values.append(item[target_column])
                
                if target_values:
                    value_counts = Counter(target_values)
                    distribution_analysis["class_counts"] = dict(value_counts)
                    
                    total = len(target_values)
                    distribution_analysis["class_proportions"] = {
                        k: v / total for k, v in value_counts.items()
                    }
                    
                    if len(value_counts) > 1:
                        max_count = max(value_counts.values())
                        min_count = min(value_counts.values())
                        distribution_analysis["imbalance_ratio"] = max_count / min_count
                        distribution_analysis["is_balanced"] = distribution_analysis["imbalance_ratio"] <= 2.0
        
        except Exception as e:
            logger.error(f"Error analyzing target distribution: {e}", exc_info=True)
        
        return distribution_analysis
    
    def _analyze_text_bias(self, data: Union[List[Dict], pd.DataFrame], text_columns: List[str]) -> Dict[str, Any]:
        """Analyze bias in text columns.
        
        Args:
            data: Data to analyze
            text_columns: List of text column names
            
        Returns:
            Text bias analysis
        """
        text_bias = {}
        
        try:
            for column in text_columns:
                column_bias = {
                    "bias_categories": {},
                    "bias_score": 0.0,
                    "total_matches": 0
                }
                
                # Extract text data
                text_data = []
                if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                    if column in data.columns:
                        text_data = data[column].dropna().astype(str).tolist()
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and column in item:
                            text_data.append(str(item[column]))
                
                if not text_data:
                    continue
                
                # Analyze each bias category
                total_text = " ".join(text_data).lower()
                total_words = len(total_text.split())
                
                for category, patterns in self.bias_patterns.items():
                    matches = 0
                    for pattern in patterns:
                        matches += len(re.findall(pattern, total_text, re.IGNORECASE))
                    
                    bias_ratio = matches / total_words if total_words > 0 else 0
                    column_bias["bias_categories"][category] = {
                        "matches": matches,
                        "ratio": bias_ratio
                    }
                    column_bias["total_matches"] += matches
                
                # Calculate overall bias score for this column
                if total_words > 0:
                    column_bias["bias_score"] = min(column_bias["total_matches"] / total_words, 1.0)
                
                text_bias[column] = column_bias
        
        except Exception as e:
            logger.error(f"Error analyzing text bias: {e}", exc_info=True)
        
        return text_bias
    
    def _analyze_duplicates(self, data: Union[List[Dict], pd.DataFrame]) -> Dict[str, Any]:
        """Analyze duplicate records in the dataset.
        
        Args:
            data: Data to analyze
            
        Returns:
            Deduplication analysis
        """
        dedup_analysis = {
            "total_records": 0,
            "unique_records": 0,
            "duplicate_records": 0,
            "duplication_rate": 0.0,
            "duplicate_groups": []
        }
        
        try:
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                dedup_analysis["total_records"] = len(data)
                
                # Find duplicates
                duplicates = data.duplicated(keep=False)
                dedup_analysis["duplicate_records"] = duplicates.sum()
                dedup_analysis["unique_records"] = len(data) - duplicates.sum()
                
                if len(data) > 0:
                    dedup_analysis["duplication_rate"] = duplicates.sum() / len(data)
                
                # Group duplicates
                if duplicates.any():
                    duplicate_data = data[duplicates]
                    grouped = duplicate_data.groupby(list(data.columns)).size().reset_index(name='count')
                    dedup_analysis["duplicate_groups"] = grouped[grouped['count'] > 1].to_dict('records')
            
            elif isinstance(data, list):
                dedup_analysis["total_records"] = len(data)
                
                # Convert to strings for comparison
                string_data = [str(item) for item in data]
                unique_strings = set(string_data)
                
                dedup_analysis["unique_records"] = len(unique_strings)
                dedup_analysis["duplicate_records"] = len(data) - len(unique_strings)
                
                if len(data) > 0:
                    dedup_analysis["duplication_rate"] = dedup_analysis["duplicate_records"] / len(data)
                
                # Find duplicate groups
                string_counts = Counter(string_data)
                duplicate_groups = [(item, count) for item, count in string_counts.items() if count > 1]
                dedup_analysis["duplicate_groups"] = duplicate_groups[:10]  # Limit to first 10
        
        except Exception as e:
            logger.error(f"Error analyzing duplicates: {e}", exc_info=True)
        
        return dedup_analysis
    
    def _analyze_text_quality(self, data: Union[List[Dict], pd.DataFrame], text_columns: List[str]) -> Dict[str, Any]:
        """Analyze text quality metrics.
        
        Args:
            data: Data to analyze
            text_columns: List of text column names
            
        Returns:
            Text quality analysis
        """
        text_analysis = {}
        
        try:
            for column in text_columns:
                column_analysis = {
                    "avg_length": 0.0,
                    "min_length": 0,
                    "max_length": 0,
                    "readability_score": 0.0,
                    "language_diversity": 0.0,
                    "empty_ratio": 0.0
                }
                
                # Extract text data
                text_data = []
                if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                    if column in data.columns:
                        text_series = data[column].dropna().astype(str)
                        text_data = text_series.tolist()
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and column in item and item[column]:
                            text_data.append(str(item[column]))
                
                if not text_data:
                    continue
                
                # Basic length statistics
                lengths = [len(text) for text in text_data]
                column_analysis["avg_length"] = statistics.mean(lengths)
                column_analysis["min_length"] = min(lengths)
                column_analysis["max_length"] = max(lengths)
                
                # Empty ratio
                total_entries = len(text_data)
                if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                    total_possible = len(data)
                    empty_count = total_possible - total_entries
                    column_analysis["empty_ratio"] = empty_count / total_possible if total_possible > 0 else 0
                
                # Readability analysis (if textstat available)
                if TEXTSTAT_AVAILABLE and text_data:
                    sample_text = " ".join(text_data[:100])  # Sample first 100 texts
                    try:
                        readability = flesch_reading_ease(sample_text)
                        column_analysis["readability_score"] = readability
                    except:
                        column_analysis["readability_score"] = 50  # Default neutral score
                
                # Language diversity (unique words ratio)
                all_words = []
                for text in text_data[:100]:  # Sample first 100 texts
                    words = re.findall(r'\b\w+\b', text.lower())
                    all_words.extend(words)
                
                if all_words:
                    unique_words = len(set(all_words))
                    total_words = len(all_words)
                    column_analysis["language_diversity"] = unique_words / total_words
                
                text_analysis[column] = column_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing text quality: {e}", exc_info=True)
        
        return text_analysis
    
    def _identify_issues(self, validation_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify issues based on validation results.
        
        Args:
            validation_report: Validation report dictionary
            
        Returns:
            List of identified issues
        """
        issues = []
        
        try:
            # Quality issues
            quality_metrics = validation_report.get("quality_metrics", {})
            
            if quality_metrics.get("completeness", 0) < self.quality_thresholds["completeness"]:
                issues.append({
                    "type": "quality",
                    "category": "completeness",
                    "severity": "high",
                    "description": f"Low data completeness: {quality_metrics['completeness']:.2f}",
                    "threshold": self.quality_thresholds["completeness"]
                })
            
            if quality_metrics.get("uniqueness", 0) < self.quality_thresholds["uniqueness"]:
                issues.append({
                    "type": "quality",
                    "category": "uniqueness",
                    "severity": "medium",
                    "description": f"Low data uniqueness: {quality_metrics['uniqueness']:.2f}",
                    "threshold": self.quality_thresholds["uniqueness"]
                })
            
            # Bias issues
            bias_analysis = validation_report.get("bias_analysis", {})
            if bias_analysis.get("bias_score", 0) > self.quality_thresholds["bias_score_max"]:
                issues.append({
                    "type": "bias",
                    "category": "overall",
                    "severity": "critical",
                    "description": f"High bias detected: {bias_analysis['bias_score']:.2f}",
                    "threshold": self.quality_thresholds["bias_score_max"]
                })
            
            # Duplication issues
            dedup_analysis = validation_report.get("deduplication_analysis", {})
            if dedup_analysis.get("duplication_rate", 0) > 0.1:  # More than 10% duplicates
                issues.append({
                    "type": "duplication",
                    "category": "high_duplication",
                    "severity": "medium",
                    "description": f"High duplication rate: {dedup_analysis['duplication_rate']:.2f}",
                    "threshold": 0.1
                })
            
            # Text quality issues
            text_analysis = validation_report.get("text_analysis", {})
            for column, analysis in text_analysis.items():
                readability = analysis.get("readability_score", 50)
                if (readability < self.quality_thresholds["readability_min"] or 
                    readability > self.quality_thresholds["readability_max"]):
                    issues.append({
                        "type": "text_quality",
                        "category": "readability",
                        "severity": "low",
                        "description": f"Poor readability in {column}: {readability:.1f}",
                        "column": column
                    })
        
        except Exception as e:
            logger.error(f"Error identifying issues: {e}", exc_info=True)
        
        return issues
    
    def _generate_recommendations(self, validation_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results.
        
        Args:
            validation_report: Validation report dictionary
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        try:
            issues = validation_report.get("issues", [])
            
            for issue in issues:
                if issue["type"] == "quality":
                    if issue["category"] == "completeness":
                        recommendations.append(
                            "Consider data imputation or removal of incomplete records"
                        )
                    elif issue["category"] == "uniqueness":
                        recommendations.append(
                            "Review data collection process to increase diversity"
                        )
                
                elif issue["type"] == "bias":
                    recommendations.append(
                        "Apply bias mitigation techniques such as data augmentation or rebalancing"
                    )
                
                elif issue["type"] == "duplication":
                    recommendations.append(
                        "Remove duplicate records to improve data quality"
                    )
                
                elif issue["type"] == "text_quality":
                    recommendations.append(
                        f"Improve text quality in column {issue.get('column', 'unknown')}"
                    )
            
            # Add general recommendations
            if not issues:
                recommendations.append("Dataset quality is good. Consider regular monitoring.")
            elif len([i for i in issues if i["severity"] == "critical"]) > 0:
                recommendations.append("Critical issues found. Address before using dataset.")
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
        
        return recommendations
    
    def _calculate_overall_score(self, validation_report: Dict[str, Any]) -> float:
        """Calculate overall validation score.
        
        Args:
            validation_report: Validation report dictionary
            
        Returns:
            Overall score between 0 and 1
        """
        try:
            scores = []
            
            # Quality score
            quality_metrics = validation_report.get("quality_metrics", {})
            quality_score = statistics.mean([
                quality_metrics.get("completeness", 0),
                quality_metrics.get("uniqueness", 0),
                quality_metrics.get("consistency", 0),
                quality_metrics.get("validity", 0)
            ])
            scores.append(quality_score)
            
            # Bias score (inverted - lower bias is better)
            bias_analysis = validation_report.get("bias_analysis", {})
            bias_score = 1 - bias_analysis.get("bias_score", 0)
            scores.append(bias_score)
            
            # Duplication score (inverted - lower duplication is better)
            dedup_analysis = validation_report.get("deduplication_analysis", {})
            duplication_rate = dedup_analysis.get("duplication_rate", 0)
            duplication_score = 1 - min(duplication_rate, 1.0)
            scores.append(duplication_score)
            
            return statistics.mean(scores) if scores else 0.0
        
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}", exc_info=True)
            return 0.0
    
    def _update_validation_stats(self, validation_report: Dict[str, Any]) -> None:
        """Update validation statistics.
        
        Args:
            validation_report: Validation report dictionary
        """
        try:
            self.validation_stats["datasets_validated"] += 1
            
            data_shape = validation_report.get("data_shape", (0, 0))
            self.validation_stats["total_records"] += data_shape[0]
            
            issues = validation_report.get("issues", [])
            self.validation_stats["quality_issues_found"] += len([
                issue for issue in issues if issue["type"] == "quality"
            ])
            self.validation_stats["bias_issues_found"] += len([
                issue for issue in issues if issue["type"] == "bias"
            ])
            
            dedup_analysis = validation_report.get("deduplication_analysis", {})
            self.validation_stats["duplicates_found"] += dedup_analysis.get("duplicate_records", 0)
            
            self.validation_stats["last_validation"] = datetime.now().isoformat()
        
        except Exception as e:
            logger.error(f"Error updating validation stats: {e}", exc_info=True)
    
    def _save_validation_report(self, validation_report: Dict[str, Any]) -> None:
        """Save validation report to file.
        
        Args:
            validation_report: Validation report dictionary
        """
        try:
            dataset_name = validation_report.get("dataset_name", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{dataset_name}_{timestamp}.json"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"Validation report saved to {filepath}")
        
        except Exception as e:
            logger.error(f"Error saving validation report: {e}", exc_info=True)
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        return self.validation_stats.copy()
    
    def update_quality_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        """Update quality thresholds.
        
        Args:
            new_thresholds: Dictionary of new threshold values
        """
        self.quality_thresholds.update(new_thresholds)
        logger.info(f"Updated quality thresholds: {new_thresholds}")
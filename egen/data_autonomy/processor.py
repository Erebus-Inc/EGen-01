"""Data processing module for the EGen platform.

This module provides components for data preprocessing,
tokenization, augmentation, and filtering.
"""

import json
import logging
import os
import random
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

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
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. Install with: pip install transformers")

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available. Install with: pip install nltk")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Data processor for the EGen platform.
    
    This class provides methods for data preprocessing,
    tokenization, augmentation, and filtering.
    """

    def __init__(
        self,
        tokenizer_name: str = "bert-base-uncased",
        max_length: int = 512,
        enable_augmentation: bool = True,
        enable_filtering: bool = True,
        save_processed: bool = True,
        output_dir: str = "./processed_data",
        processing_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the data processor.
        
        Args:
            tokenizer_name: Name of the tokenizer to use
            max_length: Maximum sequence length for tokenization
            enable_augmentation: Whether to enable data augmentation
            enable_filtering: Whether to enable data filtering
            save_processed: Whether to save processed data
            output_dir: Directory to save processed data
            processing_config: Additional processing configuration
        """
        self.tokenizer_name = tokenizer_name
        self.max_length = max_length
        self.enable_augmentation = enable_augmentation
        self.enable_filtering = enable_filtering
        self.save_processed = save_processed
        self.output_dir = output_dir
        
        # Create output directory
        if save_processed:
            os.makedirs(output_dir, exist_ok=True)
        
        # Initialize tokenizer
        self.tokenizer = None
        if TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
                logger.info(f"Loaded tokenizer: {tokenizer_name}")
            except Exception as e:
                logger.warning(f"Failed to load tokenizer {tokenizer_name}: {e}")
        
        # Processing configuration
        self.processing_config = processing_config or {
            "lowercase": True,
            "remove_punctuation": False,
            "remove_stopwords": False,
            "min_length": 10,
            "max_length": 1000,
            "remove_duplicates": True,
            "normalize_whitespace": True,
            "filter_languages": ["en"],
            "augmentation_ratio": 0.1,
            "augmentation_methods": ["synonym_replacement", "random_insertion", "random_deletion"]
        }
        
        # Initialize NLTK resources if available
        if NLTK_AVAILABLE:
            self._download_nltk_resources()
        
        # Processing statistics
        self.processing_stats = {
            "datasets_processed": 0,
            "total_records_input": 0,
            "total_records_output": 0,
            "records_filtered": 0,
            "records_augmented": 0,
            "last_processing": None
        }
    
    def _download_nltk_resources(self) -> None:
        """Download required NLTK resources."""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            logger.warning(f"Failed to download NLTK resources: {e}")
    
    def process_dataset(
        self,
        data: Union[List[Dict], pd.DataFrame, str],
        dataset_name: str = "unknown",
        text_columns: Optional[List[str]] = None,
        target_column: Optional[str] = None,
        custom_processors: Optional[List[Callable]] = None
    ) -> Dict[str, Any]:
        """Process a complete dataset.
        
        Args:
            data: Dataset to process (list of dicts, DataFrame, or file path)
            dataset_name: Name of the dataset
            text_columns: List of text column names to process
            target_column: Name of target/label column
            custom_processors: List of custom processing functions
            
        Returns:
            Processing results with processed data and statistics
        """
        logger.info(f"Starting processing of dataset: {dataset_name}")
        
        # Load data if path provided
        if isinstance(data, str):
            data = self._load_data(data)
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            if PANDAS_AVAILABLE:
                data = pd.DataFrame(data)
            else:
                logger.warning("Pandas not available, using basic processing")
        
        processing_result = {
            "dataset_name": dataset_name,
            "processing_timestamp": datetime.now().isoformat(),
            "input_shape": self._get_data_shape(data),
            "processed_data": None,
            "output_shape": (0, 0),
            "processing_steps": [],
            "statistics": {},
            "filtered_records": 0,
            "augmented_records": 0,
            "tokenization_stats": {}
        }
        
        try:
            processed_data = data.copy() if hasattr(data, 'copy') else data[:]
            
            # Step 1: Basic preprocessing
            if text_columns:
                processed_data, basic_stats = self._apply_basic_preprocessing(
                    processed_data, text_columns
                )
                processing_result["processing_steps"].append("basic_preprocessing")
                processing_result["statistics"]["basic_preprocessing"] = basic_stats
            
            # Step 2: Filtering
            if self.enable_filtering:
                processed_data, filter_stats = self._apply_filtering(
                    processed_data, text_columns
                )
                processing_result["processing_steps"].append("filtering")
                processing_result["statistics"]["filtering"] = filter_stats
                processing_result["filtered_records"] = filter_stats.get("records_removed", 0)
            
            # Step 3: Tokenization
            if text_columns and self.tokenizer:
                processed_data, tokenization_stats = self._apply_tokenization(
                    processed_data, text_columns
                )
                processing_result["processing_steps"].append("tokenization")
                processing_result["tokenization_stats"] = tokenization_stats
            
            # Step 4: Data augmentation
            if self.enable_augmentation and text_columns:
                processed_data, augmentation_stats = self._apply_augmentation(
                    processed_data, text_columns, target_column
                )
                processing_result["processing_steps"].append("augmentation")
                processing_result["statistics"]["augmentation"] = augmentation_stats
                processing_result["augmented_records"] = augmentation_stats.get("records_added", 0)
            
            # Step 5: Custom processors
            if custom_processors:
                for i, processor in enumerate(custom_processors):
                    try:
                        processed_data = processor(processed_data)
                        processing_result["processing_steps"].append(f"custom_processor_{i}")
                    except Exception as e:
                        logger.error(f"Error in custom processor {i}: {e}")
            
            # Final statistics
            processing_result["processed_data"] = processed_data
            processing_result["output_shape"] = self._get_data_shape(processed_data)
            
            # Update processing statistics
            self._update_processing_stats(processing_result)
            
            # Save processed data if enabled
            if self.save_processed:
                self._save_processed_data(processed_data, dataset_name)
            
            logger.info(
                f"Processing completed for {dataset_name}. "
                f"Input: {processing_result['input_shape']}, "
                f"Output: {processing_result['output_shape']}"
            )
            
        except Exception as e:
            logger.error(f"Error during processing: {e}", exc_info=True)
            processing_result["error"] = str(e)
        
        return processing_result
    
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
    
    def _apply_basic_preprocessing(
        self,
        data: Union[List[Dict], pd.DataFrame],
        text_columns: List[str]
    ) -> Tuple[Union[List[Dict], pd.DataFrame], Dict[str, Any]]:
        """Apply basic text preprocessing.
        
        Args:
            data: Data to preprocess
            text_columns: List of text column names
            
        Returns:
            Tuple of (processed_data, statistics)
        """
        stats = {
            "records_processed": 0,
            "columns_processed": len(text_columns),
            "transformations_applied": []
        }
        
        try:
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                for column in text_columns:
                    if column in data.columns:
                        # Apply preprocessing transformations
                        if self.processing_config.get("normalize_whitespace", True):
                            data[column] = data[column].astype(str).apply(self._normalize_whitespace)
                            stats["transformations_applied"].append("normalize_whitespace")
                        
                        if self.processing_config.get("lowercase", True):
                            data[column] = data[column].str.lower()
                            stats["transformations_applied"].append("lowercase")
                        
                        if self.processing_config.get("remove_punctuation", False):
                            data[column] = data[column].apply(self._remove_punctuation)
                            stats["transformations_applied"].append("remove_punctuation")
                        
                        if self.processing_config.get("remove_stopwords", False):
                            data[column] = data[column].apply(self._remove_stopwords)
                            stats["transformations_applied"].append("remove_stopwords")
                
                stats["records_processed"] = len(data)
            
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for column in text_columns:
                            if column in item and item[column]:
                                text = str(item[column])
                                
                                if self.processing_config.get("normalize_whitespace", True):
                                    text = self._normalize_whitespace(text)
                                
                                if self.processing_config.get("lowercase", True):
                                    text = text.lower()
                                
                                if self.processing_config.get("remove_punctuation", False):
                                    text = self._remove_punctuation(text)
                                
                                if self.processing_config.get("remove_stopwords", False):
                                    text = self._remove_stopwords(text)
                                
                                item[column] = text
                
                stats["records_processed"] = len(data)
                stats["transformations_applied"] = [
                    t for t in ["normalize_whitespace", "lowercase", "remove_punctuation", "remove_stopwords"]
                    if self.processing_config.get(t.replace("_", ""), False)
                ]
        
        except Exception as e:
            logger.error(f"Error in basic preprocessing: {e}", exc_info=True)
        
        return data, stats
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        return text.strip()
    
    def _remove_punctuation(self, text: str) -> str:
        """Remove punctuation from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without punctuation
        """
        return re.sub(r'[^\w\s]', '', text)
    
    def _remove_stopwords(self, text: str) -> str:
        """Remove stopwords from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without stopwords
        """
        if not NLTK_AVAILABLE:
            return text
        
        try:
            stop_words = set(stopwords.words('english'))
            words = word_tokenize(text)
            filtered_words = [word for word in words if word.lower() not in stop_words]
            return ' '.join(filtered_words)
        except Exception as e:
            logger.warning(f"Error removing stopwords: {e}")
            return text
    
    def _apply_filtering(
        self,
        data: Union[List[Dict], pd.DataFrame],
        text_columns: List[str]
    ) -> Tuple[Union[List[Dict], pd.DataFrame], Dict[str, Any]]:
        """Apply data filtering.
        
        Args:
            data: Data to filter
            text_columns: List of text column names
            
        Returns:
            Tuple of (filtered_data, statistics)
        """
        initial_count = len(data) if hasattr(data, '__len__') else 0
        
        stats = {
            "initial_records": initial_count,
            "final_records": 0,
            "records_removed": 0,
            "filters_applied": []
        }
        
        try:
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                # Length filtering
                min_length = self.processing_config.get("min_length", 10)
                max_length = self.processing_config.get("max_length", 1000)
                
                for column in text_columns:
                    if column in data.columns:
                        # Filter by text length
                        text_lengths = data[column].astype(str).str.len()
                        length_mask = (text_lengths >= min_length) & (text_lengths <= max_length)
                        data = data[length_mask]
                        stats["filters_applied"].append(f"length_filter_{column}")
                
                # Remove duplicates
                if self.processing_config.get("remove_duplicates", True):
                    initial_len = len(data)
                    data = data.drop_duplicates()
                    if len(data) < initial_len:
                        stats["filters_applied"].append("remove_duplicates")
                
                # Remove empty/null values
                for column in text_columns:
                    if column in data.columns:
                        data = data[data[column].notna()]
                        data = data[data[column].astype(str).str.strip() != '']
                        stats["filters_applied"].append(f"remove_empty_{column}")
            
            elif isinstance(data, list):
                filtered_data = []
                min_length = self.processing_config.get("min_length", 10)
                max_length = self.processing_config.get("max_length", 1000)
                
                seen_items = set() if self.processing_config.get("remove_duplicates", True) else None
                
                for item in data:
                    if isinstance(item, dict):
                        # Check text length constraints
                        valid_item = True
                        for column in text_columns:
                            if column in item and item[column]:
                                text_len = len(str(item[column]))
                                if text_len < min_length or text_len > max_length:
                                    valid_item = False
                                    break
                        
                        # Check for duplicates
                        if valid_item and seen_items is not None:
                            item_str = str(sorted(item.items()))
                            if item_str in seen_items:
                                valid_item = False
                            else:
                                seen_items.add(item_str)
                        
                        if valid_item:
                            filtered_data.append(item)
                
                data = filtered_data
                stats["filters_applied"] = ["length_filter", "remove_duplicates", "remove_empty"]
            
            stats["final_records"] = len(data) if hasattr(data, '__len__') else 0
            stats["records_removed"] = stats["initial_records"] - stats["final_records"]
        
        except Exception as e:
            logger.error(f"Error in filtering: {e}", exc_info=True)
        
        return data, stats
    
    def _apply_tokenization(
        self,
        data: Union[List[Dict], pd.DataFrame],
        text_columns: List[str]
    ) -> Tuple[Union[List[Dict], pd.DataFrame], Dict[str, Any]]:
        """Apply tokenization to text data.
        
        Args:
            data: Data to tokenize
            text_columns: List of text column names
            
        Returns:
            Tuple of (tokenized_data, statistics)
        """
        stats = {
            "records_tokenized": 0,
            "columns_tokenized": 0,
            "avg_token_length": 0.0,
            "max_token_length": 0,
            "truncated_sequences": 0
        }
        
        if not self.tokenizer:
            logger.warning("No tokenizer available, skipping tokenization")
            return data, stats
        
        try:
            token_lengths = []
            
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                for column in text_columns:
                    if column in data.columns:
                        tokenized_column = f"{column}_tokens"
                        input_ids_column = f"{column}_input_ids"
                        attention_mask_column = f"{column}_attention_mask"
                        
                        # Tokenize texts
                        texts = data[column].astype(str).tolist()
                        tokenized = self.tokenizer(
                            texts,
                            padding=True,
                            truncation=True,
                            max_length=self.max_length,
                            return_tensors=None
                        )
                        
                        # Add tokenized data to DataFrame
                        data[input_ids_column] = tokenized['input_ids']
                        data[attention_mask_column] = tokenized['attention_mask']
                        
                        # Calculate statistics
                        for input_ids in tokenized['input_ids']:
                            token_length = len(input_ids)
                            token_lengths.append(token_length)
                            if token_length == self.max_length:
                                stats["truncated_sequences"] += 1
                        
                        stats["columns_tokenized"] += 1
                
                stats["records_tokenized"] = len(data)
            
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for column in text_columns:
                            if column in item and item[column]:
                                text = str(item[column])
                                
                                # Tokenize text
                                tokenized = self.tokenizer(
                                    text,
                                    padding=True,
                                    truncation=True,
                                    max_length=self.max_length,
                                    return_tensors=None
                                )
                                
                                # Add tokenized data
                                item[f"{column}_input_ids"] = tokenized['input_ids']
                                item[f"{column}_attention_mask"] = tokenized['attention_mask']
                                
                                # Calculate statistics
                                token_length = len(tokenized['input_ids'])
                                token_lengths.append(token_length)
                                if token_length == self.max_length:
                                    stats["truncated_sequences"] += 1
                
                stats["records_tokenized"] = len(data)
                stats["columns_tokenized"] = len(text_columns)
            
            # Calculate token statistics
            if token_lengths:
                stats["avg_token_length"] = sum(token_lengths) / len(token_lengths)
                stats["max_token_length"] = max(token_lengths)
        
        except Exception as e:
            logger.error(f"Error in tokenization: {e}", exc_info=True)
        
        return data, stats
    
    def _apply_augmentation(
        self,
        data: Union[List[Dict], pd.DataFrame],
        text_columns: List[str],
        target_column: Optional[str] = None
    ) -> Tuple[Union[List[Dict], pd.DataFrame], Dict[str, Any]]:
        """Apply data augmentation.
        
        Args:
            data: Data to augment
            text_columns: List of text column names
            target_column: Name of target/label column
            
        Returns:
            Tuple of (augmented_data, statistics)
        """
        initial_count = len(data) if hasattr(data, '__len__') else 0
        augmentation_ratio = self.processing_config.get("augmentation_ratio", 0.1)
        augmentation_methods = self.processing_config.get("augmentation_methods", ["synonym_replacement"])
        
        stats = {
            "initial_records": initial_count,
            "records_added": 0,
            "final_records": 0,
            "augmentation_methods": augmentation_methods,
            "augmentation_ratio": augmentation_ratio
        }
        
        try:
            # Calculate number of records to augment
            num_to_augment = int(initial_count * augmentation_ratio)
            
            if num_to_augment == 0:
                stats["final_records"] = initial_count
                return data, stats
            
            augmented_records = []
            
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                # Sample records for augmentation
                sample_indices = random.sample(range(len(data)), min(num_to_augment, len(data)))
                
                for idx in sample_indices:
                    original_record = data.iloc[idx].copy()
                    
                    # Apply augmentation to text columns
                    for column in text_columns:
                        if column in original_record and pd.notna(original_record[column]):
                            original_text = str(original_record[column])
                            augmented_text = self._augment_text(original_text, augmentation_methods)
                            original_record[column] = augmented_text
                    
                    augmented_records.append(original_record)
                
                # Add augmented records to DataFrame
                if augmented_records:
                    augmented_df = pd.DataFrame(augmented_records)
                    data = pd.concat([data, augmented_df], ignore_index=True)
            
            elif isinstance(data, list):
                # Sample records for augmentation
                sample_indices = random.sample(range(len(data)), min(num_to_augment, len(data)))
                
                for idx in sample_indices:
                    if isinstance(data[idx], dict):
                        original_record = data[idx].copy()
                        
                        # Apply augmentation to text columns
                        for column in text_columns:
                            if column in original_record and original_record[column]:
                                original_text = str(original_record[column])
                                augmented_text = self._augment_text(original_text, augmentation_methods)
                                original_record[column] = augmented_text
                        
                        augmented_records.append(original_record)
                
                # Add augmented records to list
                data.extend(augmented_records)
            
            stats["records_added"] = len(augmented_records)
            stats["final_records"] = len(data) if hasattr(data, '__len__') else 0
        
        except Exception as e:
            logger.error(f"Error in augmentation: {e}", exc_info=True)
        
        return data, stats
    
    def _augment_text(self, text: str, methods: List[str]) -> str:
        """Augment a single text using specified methods.
        
        Args:
            text: Original text
            methods: List of augmentation methods to apply
            
        Returns:
            Augmented text
        """
        augmented_text = text
        
        try:
            # Apply random augmentation method
            method = random.choice(methods)
            
            if method == "synonym_replacement":
                augmented_text = self._synonym_replacement(text)
            elif method == "random_insertion":
                augmented_text = self._random_insertion(text)
            elif method == "random_deletion":
                augmented_text = self._random_deletion(text)
            elif method == "random_swap":
                augmented_text = self._random_swap(text)
            else:
                # Default: slight modification
                augmented_text = self._random_deletion(text)
        
        except Exception as e:
            logger.warning(f"Error in text augmentation: {e}")
            augmented_text = text
        
        return augmented_text
    
    def _synonym_replacement(self, text: str, n: int = 1) -> str:
        """Replace n words with synonyms.
        
        Args:
            text: Original text
            n: Number of words to replace
            
        Returns:
            Text with synonym replacements
        """
        if not NLTK_AVAILABLE:
            return text
        
        try:
            from nltk.corpus import wordnet
            
            words = word_tokenize(text)
            new_words = words.copy()
            random_word_list = list(set([word for word in words if word.isalpha()]))
            random.shuffle(random_word_list)
            
            num_replaced = 0
            for random_word in random_word_list:
                synonyms = []
                for syn in wordnet.synsets(random_word):
                    for lemma in syn.lemmas():
                        synonyms.append(lemma.name())
                
                if synonyms:
                    synonym = random.choice(synonyms)
                    new_words = [synonym if word == random_word else word for word in new_words]
                    num_replaced += 1
                
                if num_replaced >= n:
                    break
            
            return ' '.join(new_words)
        
        except Exception as e:
            logger.warning(f"Error in synonym replacement: {e}")
            return text
    
    def _random_insertion(self, text: str, n: int = 1) -> str:
        """Randomly insert n words into the text.
        
        Args:
            text: Original text
            n: Number of words to insert
            
        Returns:
            Text with random insertions
        """
        if not NLTK_AVAILABLE:
            return text
        
        try:
            from nltk.corpus import wordnet
            
            words = word_tokenize(text)
            
            for _ in range(n):
                # Get a random word from the text
                random_word = random.choice([word for word in words if word.isalpha()])
                
                # Get synonyms
                synonyms = []
                for syn in wordnet.synsets(random_word):
                    for lemma in syn.lemmas():
                        synonyms.append(lemma.name())
                
                if synonyms:
                    random_synonym = random.choice(synonyms)
                    random_idx = random.randint(0, len(words))
                    words.insert(random_idx, random_synonym)
            
            return ' '.join(words)
        
        except Exception as e:
            logger.warning(f"Error in random insertion: {e}")
            return text
    
    def _random_deletion(self, text: str, p: float = 0.1) -> str:
        """Randomly delete words with probability p.
        
        Args:
            text: Original text
            p: Probability of deleting each word
            
        Returns:
            Text with random deletions
        """
        try:
            words = text.split()
            
            if len(words) == 1:
                return text
            
            new_words = []
            for word in words:
                if random.random() > p:
                    new_words.append(word)
            
            # If all words are deleted, return original
            if not new_words:
                return text
            
            return ' '.join(new_words)
        
        except Exception as e:
            logger.warning(f"Error in random deletion: {e}")
            return text
    
    def _random_swap(self, text: str, n: int = 1) -> str:
        """Randomly swap n pairs of words.
        
        Args:
            text: Original text
            n: Number of swaps to perform
            
        Returns:
            Text with random swaps
        """
        try:
            words = text.split()
            
            if len(words) < 2:
                return text
            
            for _ in range(n):
                idx1, idx2 = random.sample(range(len(words)), 2)
                words[idx1], words[idx2] = words[idx2], words[idx1]
            
            return ' '.join(words)
        
        except Exception as e:
            logger.warning(f"Error in random swap: {e}")
            return text
    
    def _update_processing_stats(self, processing_result: Dict[str, Any]) -> None:
        """Update processing statistics.
        
        Args:
            processing_result: Processing result dictionary
        """
        try:
            self.processing_stats["datasets_processed"] += 1
            
            input_shape = processing_result.get("input_shape", (0, 0))
            output_shape = processing_result.get("output_shape", (0, 0))
            
            self.processing_stats["total_records_input"] += input_shape[0]
            self.processing_stats["total_records_output"] += output_shape[0]
            self.processing_stats["records_filtered"] += processing_result.get("filtered_records", 0)
            self.processing_stats["records_augmented"] += processing_result.get("augmented_records", 0)
            
            self.processing_stats["last_processing"] = datetime.now().isoformat()
        
        except Exception as e:
            logger.error(f"Error updating processing stats: {e}", exc_info=True)
    
    def _save_processed_data(self, data: Union[List[Dict], pd.DataFrame], dataset_name: str) -> None:
        """Save processed data to file.
        
        Args:
            data: Processed data
            dataset_name: Name of the dataset
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                filename = f"processed_{dataset_name}_{timestamp}.csv"
                filepath = os.path.join(self.output_dir, filename)
                data.to_csv(filepath, index=False)
            else:
                filename = f"processed_{dataset_name}_{timestamp}.json"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            logger.info(f"Processed data saved to {filepath}")
        
        except Exception as e:
            logger.error(f"Error saving processed data: {e}", exc_info=True)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return self.processing_stats.copy()
    
    def update_processing_config(self, new_config: Dict[str, Any]) -> None:
        """Update processing configuration.
        
        Args:
            new_config: Dictionary of new configuration values
        """
        self.processing_config.update(new_config)
        logger.info(f"Updated processing config: {new_config}")
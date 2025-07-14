Data Autonomy Engine
=================

Overview
--------

The Data Autonomy Engine is a core component of the EGen platform that manages datasets and training data. It enables autonomous data discovery, validation, preprocessing, and versioning to ensure high-quality training data for the THL-150 model.

Architecture
-----------

.. code-block::

    Data Autonomy Engine
    ├── Dataset Discovery
    │   ├── Hugging Face Hub Connector
    │   ├── Web Crawler
    │   └── Local Dataset Scanner
    ├── Data Validation
    │   ├── Quality Checker
    │   ├── Bias Detector
    │   └── Duplication Analyzer
    ├── Data Preprocessing
    │   ├── Tokenization
    │   ├── Augmentation
    │   └── Filtering
    └── Data Management
        ├── Version Control
        ├── Metadata Tracking
        └── Storage Optimization

Components
---------

Dataset Discovery
~~~~~~~~~~~~~~~

The Dataset Discovery component finds and retrieves relevant datasets:

- **Hugging Face Hub Connector**: Searches and downloads datasets from Hugging Face
- **Web Crawler**: Collects data from websites, documentation, and open-source repositories
- **Local Dataset Scanner**: Identifies and indexes local data sources

Data Validation
~~~~~~~~~~~~~

The Data Validation component ensures data quality and integrity:

- **Quality Checker**: Verifies data format, completeness, and consistency
- **Bias Detector**: Identifies and mitigates biases in training data
- **Duplication Analyzer**: Detects and removes duplicate or near-duplicate samples

Data Preprocessing
~~~~~~~~~~~~~~~

The Data Preprocessing component prepares data for training:

- **Tokenization**: Converts text to token sequences using appropriate tokenizers
- **Augmentation**: Generates additional training samples through transformations
- **Filtering**: Removes low-quality or irrelevant samples

Data Management
~~~~~~~~~~~~~

The Data Management component organizes and tracks datasets:

- **Version Control**: Maintains dataset versions and change history
- **Metadata Tracking**: Records dataset statistics, sources, and usage
- **Storage Optimization**: Compresses and efficiently stores large datasets

API Reference
------------

Dataset Discovery
~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.data_autonomy.discovery import DatasetDiscovery
    
    # Initialize discovery
    discovery = DatasetDiscovery(
        hf_token="YOUR_HUGGINGFACE_TOKEN",  # Optional
        cache_dir="/path/to/cache"
    )
    
    # Search Hugging Face Hub
    datasets = discovery.search_hub(
        query="code",
        task_type="text-generation",
        min_size=1000000,  # 1M samples
        languages=["python", "javascript"]
    )
    
    # Download dataset
    dataset = discovery.download_dataset("codeparrot/github-code")
    
    # Crawl web for data
    web_dataset = discovery.crawl_web(
        urls=["https://github.com/Erebus-Inc/EGen-01.git"],
        file_types=[".py", ".js"],
        max_files=1000
    )
    
    # Scan local directory
    local_dataset = discovery.scan_local(
        directory="/path/to/code",
        file_types=[".py", ".js"],
        recursive=True
    )

Data Validation
~~~~~~~~~~~~~

.. code-block:: python

    from egen.data_autonomy.validation import DataValidator
    
    # Initialize validator
    validator = DataValidator()
    
    # Check data quality
    quality_report = validator.check_quality(dataset)
    
    # Detect bias
    bias_report = validator.detect_bias(
        dataset,
        sensitive_attributes=["gender", "ethnicity"],
        metrics=["statistical_parity", "equal_opportunity"]
    )
    
    # Analyze duplications
    duplication_report = validator.analyze_duplications(
        dataset,
        method="minhash",  # or "exact", "simhash"
        threshold=0.9
    )
    
    # Clean dataset
    clean_dataset = validator.clean_dataset(
        dataset,
        remove_duplicates=True,
        fix_formatting=True,
        balance_classes=True
    )

Data Preprocessing
~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.data_autonomy.preprocessing import DataPreprocessor
    
    # Initialize preprocessor
    preprocessor = DataPreprocessor(
        tokenizer_path="/path/to/tokenizer"
    )
    
    # Tokenize dataset
    tokenized_dataset = preprocessor.tokenize(
        dataset,
        max_length=1024,
        add_special_tokens=True
    )
    
    # Augment dataset
    augmented_dataset = preprocessor.augment(
        dataset,
        methods=["synonym_replacement", "back_translation"],
        augmentation_factor=2.0
    )
    
    # Filter dataset
    filtered_dataset = preprocessor.filter(
        dataset,
        min_length=10,
        max_length=1000,
        quality_threshold=0.8
    )
    
    # Create training splits
    train_dataset, val_dataset, test_dataset = preprocessor.create_splits(
        dataset,
        train_ratio=0.8,
        val_ratio=0.1,
        test_ratio=0.1,
        stratify_by="domain"
    )

Data Management
~~~~~~~~~~~~~

.. code-block:: python

    from egen.data_autonomy.management import DataManager
    
    # Initialize manager
    manager = DataManager(
        storage_path="/path/to/storage"
    )
    
    # Save dataset version
    version_id = manager.save_version(
        dataset,
        name="code-dataset",
        version="1.0.0",
        metadata={
            "source": "github",
            "samples": 1000000,
            "languages": ["python", "javascript"]
        }
    )
    
    # Load dataset version
    loaded_dataset = manager.load_version(
        name="code-dataset",
        version="1.0.0"  # or version_id
    )
    
    # List available datasets
    datasets = manager.list_datasets()
    
    # Get dataset versions
    versions = manager.get_versions("code-dataset")
    
    # Compare dataset versions
    diff = manager.compare_versions(
        name="code-dataset",
        version_a="1.0.0",
        version_b="1.1.0"
    )

Configuration
-------------

The Data Autonomy Engine can be configured through a YAML configuration file:

.. code-block:: yaml

    # data_autonomy_config.yaml
    
    discovery:
      hub_enabled: true
      hub_token: "${HUGGINGFACE_API_KEY}"  # Environment variable
      web_crawler:
        enabled: true
        max_pages_per_site: 1000
        respect_robots_txt: true
        user_agent: "EGen Data Crawler/1.0"
      local_scanner:
        enabled: true
        default_directories:
          - "/path/to/data1"
          - "/path/to/data2"
    
    validation:
      quality_checks:
        - format_validation
        - completeness
        - consistency
      bias_detection:
        enabled: true
        sensitive_attributes:
          - gender
          - ethnicity
          - age
        metrics:
          - statistical_parity
          - equal_opportunity
      duplication_analysis:
        method: "minhash"
        threshold: 0.9
        index_path: "/path/to/duplication_index"
    
    preprocessing:
      tokenizer_path: "/path/to/tokenizer"
      default_max_length: 1024
      augmentation:
        enabled: true
        methods:
          - synonym_replacement
          - back_translation
        augmentation_factor: 1.5
      filtering:
        min_length: 10
        max_length: 2048
        quality_threshold: 0.7
    
    management:
      storage_path: "/path/to/storage"
      compression: true
      compression_level: 9
      metadata_db_path: "/path/to/metadata.db"
      backup_enabled: true
      backup_frequency: "daily"

Usage Examples
-------------

End-to-End Data Pipeline
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.data_autonomy import (
        DatasetDiscovery,
        DataValidator,
        DataPreprocessor,
        DataManager
    )
    
    # Initialize components
    discovery = DatasetDiscovery()
    validator = DataValidator()
    preprocessor = DataPreprocessor()
    manager = DataManager()
    
    # Step 1: Discover datasets
    raw_dataset = discovery.search_hub(query="code", task_type="text-generation")
    
    # Step 2: Validate and clean
    clean_dataset = validator.clean_dataset(
        raw_dataset,
        remove_duplicates=True,
        fix_formatting=True
    )
    
    # Step 3: Preprocess
    processed_dataset = preprocessor.tokenize(clean_dataset)
    train_dataset, val_dataset, test_dataset = preprocessor.create_splits(processed_dataset)
    
    # Step 4: Save versions
    manager.save_version(train_dataset, name="code-train", version="1.0.0")
    manager.save_version(val_dataset, name="code-val", version="1.0.0")
    manager.save_version(test_dataset, name="code-test", version="1.0.0")

Continuous Data Collection
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.data_autonomy import DatasetDiscovery, DataManager
    import schedule
    import time
    
    discovery = DatasetDiscovery()
    manager = DataManager()
    
    def collect_new_data():
        # Get current date for versioning
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Collect new data from web
        new_data = discovery.crawl_web(
            urls=["https://github.com/trending/python"],
            file_types=[".py"],
            max_files=100
        )
        
        # Save as new version
        manager.save_version(
            new_data,
            name="daily-python-trending",
            version=date_str
        )
        
        print(f"Collected {len(new_data)} new samples on {date_str}")
    
    # Schedule daily collection
    schedule.every().day.at("02:00").do(collect_new_data)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

Custom Data Pipeline
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.data_autonomy import DataPreprocessor
    from egen.data_autonomy.validation import CustomValidator
    
    class CodeQualityValidator(CustomValidator):
        def validate(self, dataset):
            # Custom validation for code quality
            valid_samples = []
            for sample in dataset:
                # Check for syntax errors
                if self.check_syntax(sample["code"]):
                    # Check for code style
                    if self.check_style(sample["code"]):
                        valid_samples.append(sample)
            return valid_samples
        
        def check_syntax(self, code):
            # Implementation of syntax checking
            try:
                compile(code, "<string>", "exec")
                return True
            except SyntaxError:
                return False
        
        def check_style(self, code):
            # Implementation of style checking
            # ...
            return True
    
    # Use custom validator in pipeline
    validator = CodeQualityValidator()
    preprocessor = DataPreprocessor()
    
    # Process dataset with custom validation
    valid_samples = validator.validate(dataset)
    processed_dataset = preprocessor.tokenize(valid_samples)
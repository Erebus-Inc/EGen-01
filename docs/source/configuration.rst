Configuration
=============

This guide provides comprehensive information on configuring the EGen Platform, including environment variables, configuration files, and best practices.

Configuration Methods
-------------------

The EGen Platform supports multiple configuration methods, listed here in order of precedence (highest to lowest):

1. **Command-line Arguments**: Highest priority, override all other settings
2. **Environment Variables**: Override configuration files
3. **Configuration Files**: YAML or JSON files with structured configuration
4. **Default Values**: Used when no other configuration is provided

Command-line Arguments
-------------------

The EGen Platform CLI supports various command-line arguments for configuration:

.. code-block:: bash

   # Start the API server with custom settings
   python -m egen.api.main --host 0.0.0.0 --port 8000 --workers 4 --log-level info
   
   # Start the web interface with custom settings
   python -m egen.web.main --port 8501 --api-url http://localhost:8000
   
   # Load a specific model
   python -m egen.cli.model load --model-path /path/to/model --quantization int8

Common command-line arguments:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Argument
     - Default
     - Description
   * - ``--config-file``
     - ``config/egen.yml``
     - Path to configuration file
   * - ``--host``
     - ``127.0.0.1``
     - Host to bind the server to
   * - ``--port``
     - ``8000``
     - Port to bind the server to
   * - ``--workers``
     - ``1``
     - Number of worker processes
   * - ``--log-level``
     - ``info``
     - Logging level (debug, info, warning, error)
   * - ``--env``
     - ``development``
     - Environment (development, testing, production)

Environment Variables
------------------

Environment variables can be used to configure the EGen Platform:

.. code-block:: bash

   # Core settings
   export EGEN_ENV=production
   export EGEN_LOG_LEVEL=info
   export EGEN_CONFIG_PATH=/path/to/config/egen.yml
   
   # API settings
   export EGEN_API_HOST=0.0.0.0
   export EGEN_API_PORT=8000
   export EGEN_API_WORKERS=4
   export EGEN_API_TIMEOUT=60
   
   # Web settings
   export EGEN_WEB_PORT=8501
   export EGEN_API_URL=http://localhost:8000
   
   # Database settings
   export EGEN_DB_URI=postgresql://user:password@localhost:5432/egen
   export EGEN_DB_POOL_SIZE=10
   export EGEN_DB_MAX_OVERFLOW=20
   
   # Redis settings
   export EGEN_REDIS_URI=redis://localhost:6379/0
   export EGEN_REDIS_POOL_SIZE=10
   
   # Model settings
   export EGEN_MODEL_PATH=/path/to/models
   export EGEN_DEFAULT_MODEL=THL-150
   export EGEN_MODEL_QUANTIZATION=int8
   
   # Security settings
   export EGEN_SECRET_KEY=your-secret-key
   export EGEN_ENABLE_AUTH=true
   export EGEN_AUTH_PROVIDER=jwt
   export EGEN_CORS_ORIGINS=http://localhost:3000,https://example.com

Environment variables follow a naming convention:

1. All variables are prefixed with ``EGEN_``
2. Sections are separated by underscores
3. Names are in uppercase

Configuration Files
-----------------

The EGen Platform supports YAML and JSON configuration files for more complex configurations.

YAML Configuration
~~~~~~~~~~~~~~~

YAML is the recommended format for configuration files:

.. code-block:: yaml

   # config/egen.yml
   environment: production
   
   logging:
     level: info
     format: json
     output: stdout
     file: /var/log/egen/api.log
   
   api:
     host: 0.0.0.0
     port: 8000
     workers: 4
     timeout: 60
     rate_limit: 100
     cors_origins:
       - http://localhost:3000
       - https://example.com
   
   web:
     port: 8501
     theme: light
     api_url: http://localhost:8000
   
   database:
     uri: postgresql://user:password@localhost:5432/egen
     pool_size: 10
     max_overflow: 20
     pool_timeout: 30
   
   redis:
     uri: redis://localhost:6379/0
     pool_size: 10
   
   model:
     path: /path/to/models
     default: THL-150
     quantization: int8
     batch_size: 4
     max_length: 2048
   
   security:
     enable_auth: true
     auth_provider: jwt
     secret_key: your-secret-key
     token_expiry: 86400

JSON Configuration
~~~~~~~~~~~~~~~

JSON configuration is also supported:

.. code-block:: json

   {
     "environment": "production",
     
     "logging": {
       "level": "info",
       "format": "json",
       "output": "stdout",
       "file": "/var/log/egen/api.log"
     },
     
     "api": {
       "host": "0.0.0.0",
       "port": 8000,
       "workers": 4,
       "timeout": 60,
       "rate_limit": 100,
       "cors_origins": [
         "http://localhost:3000",
         "https://example.com"
       ]
     },
     
     "web": {
       "port": 8501,
       "theme": "light",
       "api_url": "http://localhost:8000"
     },
     
     "database": {
       "uri": "postgresql://user:password@localhost:5432/egen",
       "pool_size": 10,
       "max_overflow": 20,
       "pool_timeout": 30
     },
     
     "redis": {
       "uri": "redis://localhost:6379/0",
       "pool_size": 10
     },
     
     "model": {
       "path": "/path/to/models",
       "default": "THL-150",
       "quantization": "int8",
       "batch_size": 4,
       "max_length": 2048
     },
     
     "security": {
       "enable_auth": true,
       "auth_provider": "jwt",
       "secret_key": "your-secret-key",
       "token_expiry": 86400
     }
   }

Loading Configuration
------------------

The EGen Platform provides utilities for loading and managing configuration:

.. code-block:: python

   from egen.config import load_config, get_config
   
   # Load configuration from file
   config = load_config("/path/to/config/egen.yml")
   
   # Access configuration values
   api_port = config.api.port
   db_uri = config.database.uri
   
   # Get configuration with fallback
   log_level = config.get("logging.level", default="info")
   
   # Get global configuration (after it's been loaded)
   config = get_config()
   model_path = config.model.path

Configuration Sections
--------------------

Core Settings
~~~~~~~~~~~

Core settings control the general behavior of the EGen Platform:

.. code-block:: yaml

   # Core settings
   environment: production  # production, development, testing
   debug: false             # Enable debug mode
   timezone: UTC            # Default timezone

Logging Settings
~~~~~~~~~~~~~~

Logging settings control how the EGen Platform logs information:

.. code-block:: yaml

   # Logging settings
   logging:
     level: info            # debug, info, warning, error
     format: json           # json, text
     output: stdout         # stdout, file, both
     file: /var/log/egen/api.log
     rotation: daily        # none, hourly, daily, weekly
     retention: 30          # Number of days to keep logs
     compress: true         # Compress rotated logs

API Settings
~~~~~~~~~~

API settings control the behavior of the API server:

.. code-block:: yaml

   # API settings
   api:
     host: 0.0.0.0          # Host to bind to
     port: 8000             # Port to bind to
     workers: 4             # Number of worker processes
     timeout: 60            # Request timeout in seconds
     rate_limit: 100        # Requests per minute per client
     cors_origins:          # Allowed CORS origins
       - http://localhost:3000
       - https://example.com
     docs_url: /docs        # URL for API documentation
     redoc_url: /redoc      # URL for ReDoc documentation
     openapi_url: /openapi.json  # URL for OpenAPI schema
     root_path: /api/v1     # Root path for all endpoints

Web Settings
~~~~~~~~~~

Web settings control the behavior of the web interface:

.. code-block:: yaml

   # Web settings
   web:
     port: 8501             # Port to bind to
     theme: light           # light, dark, custom
     api_url: http://localhost:8000  # URL of the API server
     page_title: EGen Platform  # Title of the web page
     favicon: /static/favicon.ico  # Path to favicon
     allow_uploads: true    # Allow file uploads
     max_upload_size: 10    # Maximum upload size in MB
     session_expiry: 7      # Session expiry in days

Database Settings
~~~~~~~~~~~~~~

Database settings control the connection to the database:

.. code-block:: yaml

   # Database settings
   database:
     uri: postgresql://user:password@localhost:5432/egen
     pool_size: 10          # Maximum connections in pool
     max_overflow: 20       # Maximum overflow connections
     pool_timeout: 30       # Seconds to wait for connection
     pool_recycle: 1800     # Recycle connections after 30 minutes
     echo: false            # Log SQL queries
     schema: public         # Database schema
     ssl: false             # Use SSL for connection
     ssl_ca: /path/to/ca.pem  # SSL CA certificate
     ssl_cert: /path/to/cert.pem  # SSL client certificate
     ssl_key: /path/to/key.pem  # SSL client key

Redis Settings
~~~~~~~~~~~~

Redis settings control the connection to Redis:

.. code-block:: yaml

   # Redis settings
   redis:
     uri: redis://localhost:6379/0
     pool_size: 10          # Maximum connections in pool
     socket_timeout: 5      # Socket timeout in seconds
     socket_connect_timeout: 5  # Socket connect timeout in seconds
     retry_on_timeout: true  # Retry on timeout
     health_check_interval: 30  # Health check interval in seconds
     ssl: false             # Use SSL for connection
     ssl_ca: /path/to/ca.pem  # SSL CA certificate
     ssl_cert: /path/to/cert.pem  # SSL client certificate
     ssl_key: /path/to/key.pem  # SSL client key

Model Settings
~~~~~~~~~~~~

Model settings control the behavior of the THL-150 model:

.. code-block:: yaml

   # Model settings
   model:
     path: /path/to/models  # Path to model files
     default: THL-150       # Default model to load
     quantization: int8     # none, fp16, int8, int4
     batch_size: 4          # Batch size for inference
     max_length: 2048       # Maximum output length
     temperature: 0.7       # Sampling temperature
     top_p: 0.9             # Top-p sampling parameter
     top_k: 40              # Top-k sampling parameter
     repetition_penalty: 1.1  # Repetition penalty
     cache_size: 1000       # Size of response cache
     use_cuda_graphs: true  # Use CUDA graphs for optimization
     optimize_for_inference: true  # Apply inference optimizations
     use_flash_attention: true  # Use flash attention
     domain_routing:        # Domain routing configuration
       enabled: true        # Enable domain routing
       threshold: 0.7       # Confidence threshold for routing
       domains:             # Available domains
         - code
         - math
         - security
         - general

Security Settings
~~~~~~~~~~~~~~

Security settings control authentication and authorization:

.. code-block:: yaml

   # Security settings
   security:
     enable_auth: true      # Enable authentication
     auth_provider: jwt     # jwt, oauth, api_key
     secret_key: your-secret-key  # Secret key for JWT
     token_expiry: 86400    # Token expiry in seconds
     refresh_token_expiry: 604800  # Refresh token expiry in seconds
     password_policy:       # Password policy
       min_length: 12       # Minimum password length
       require_uppercase: true  # Require uppercase letters
       require_lowercase: true  # Require lowercase letters
       require_numbers: true  # Require numbers
       require_special_chars: true  # Require special characters
       max_age_days: 90     # Password expiry in days
       history_count: 5     # Remember last N passwords
     oauth:                 # OAuth configuration
       providers:           # OAuth providers
         google:            # Google OAuth
           client_id: your-client-id
           client_secret: your-client-secret
           redirect_uri: http://localhost:8000/auth/google/callback
         github:            # GitHub OAuth
           client_id: your-client-id
           client_secret: your-client-secret
           redirect_uri: http://localhost:8000/auth/github/callback
     rate_limiting:         # Rate limiting
       enabled: true        # Enable rate limiting
       strategy: fixed_window  # fixed_window, sliding_window, token_bucket
       storage: redis       # memory, redis
       default_limit: 100   # Default requests per minute
       limits:              # Custom limits by endpoint
         /v1/generate: 60   # 60 requests per minute
         /v1/assistant/query: 30  # 30 requests per minute

Self-Healing Settings
~~~~~~~~~~~~~~~~~

Self-healing settings control the behavior of the self-healing system:

.. code-block:: yaml

   # Self-healing settings
   self_healing:
     enabled: true          # Enable self-healing
     check_interval: 60     # Check interval in seconds
     monitors:              # Monitors to enable
       - memory_usage       # Monitor memory usage
       - cpu_usage          # Monitor CPU usage
       - gpu_usage          # Monitor GPU usage
       - disk_usage         # Monitor disk usage
       - model_performance  # Monitor model performance
       - api_latency        # Monitor API latency
       - error_rate         # Monitor error rate
     thresholds:            # Thresholds for alerts
       memory_usage: 90     # Alert at 90% memory usage
       cpu_usage: 80        # Alert at 80% CPU usage
       gpu_usage: 85        # Alert at 85% GPU usage
       disk_usage: 85       # Alert at 85% disk usage
       model_latency: 2000  # Alert at 2000ms model latency
       api_latency: 1000    # Alert at 1000ms API latency
       error_rate: 5        # Alert at 5% error rate
     actions:               # Actions to take on threshold breach
       memory_usage:        # Actions for memory usage
         - clear_cache      # Clear cache
         - restart_service  # Restart service
       cpu_usage:           # Actions for CPU usage
         - throttle_requests  # Throttle incoming requests
       gpu_usage:           # Actions for GPU usage
         - optimize_batch_size  # Optimize batch size
       model_performance:   # Actions for model performance
         - reload_model     # Reload model

Self-Optimization Settings
~~~~~~~~~~~~~~~~~~~~~~

Self-optimization settings control the behavior of the self-optimization system:

.. code-block:: yaml

   # Self-optimization settings
   self_optimization:
     enabled: true          # Enable self-optimization
     schedule: "0 2 * * *"  # Cron schedule (2 AM daily)
     strategies:            # Optimization strategies
       hyperparameter:      # Hyperparameter optimization
         enabled: true      # Enable hyperparameter optimization
         method: bayesian   # bayesian, random, grid
         max_trials: 20     # Maximum number of trials
         parameters:        # Parameters to optimize
           temperature:     # Temperature parameter
             min: 0.1
             max: 1.0
           top_p:           # Top-p parameter
             min: 0.5
             max: 1.0
       nas:                 # Neural architecture search
         enabled: false     # Enable neural architecture search
         method: evolution  # evolution, reinforcement
         max_trials: 10     # Maximum number of trials
       pruning:             # Model pruning
         enabled: true      # Enable model pruning
         method: magnitude  # magnitude, structured
         sparsity: 0.3     # Target sparsity
       quantization:        # Model quantization
         enabled: true      # Enable model quantization
         method: int8       # fp16, int8, int4

Data Autonomy Settings
~~~~~~~~~~~~~~~~~~

Data autonomy settings control the behavior of the data autonomy engine:

.. code-block:: yaml

   # Data autonomy settings
   data_autonomy:
     enabled: true          # Enable data autonomy
     schedule: "0 3 * * *"  # Cron schedule (3 AM daily)
     discovery:             # Dataset discovery
       enabled: true        # Enable dataset discovery
       sources:             # Data sources
         - path: /path/to/data  # Local path
           type: file       # file, database, api
         - url: https://example.com/api/data  # API URL
           type: api        # file, database, api
           auth_token: your-auth-token  # Authentication token
     validation:            # Data validation
       enabled: true        # Enable data validation
       schema_path: /path/to/schemas  # Path to JSON schemas
       rules:               # Validation rules
         - name: missing_values  # Check for missing values
           threshold: 0.1   # Maximum allowed missing values
         - name: outliers   # Check for outliers
           threshold: 0.05  # Maximum allowed outliers
     preprocessing:         # Data preprocessing
       enabled: true        # Enable data preprocessing
       steps:               # Preprocessing steps
         - name: normalize  # Normalize data
           columns: ["feature1", "feature2"]  # Columns to normalize
         - name: one_hot_encode  # One-hot encode categorical data
           columns: ["category1", "category2"]  # Columns to encode

Monitoring Settings
~~~~~~~~~~~~~~~~

Monitoring settings control the behavior of the monitoring system:

.. code-block:: yaml

   # Monitoring settings
   monitoring:
     enabled: true          # Enable monitoring
     metrics:               # Metrics collection
       enabled: true        # Enable metrics collection
       port: 9090           # Prometheus metrics port
       path: /metrics       # Metrics endpoint path
       collect_interval: 15  # Collection interval in seconds
     logging:               # Logging configuration
       enabled: true        # Enable logging
       format: json         # json, text
       output: file         # stdout, file, both
       file: /var/log/egen/monitoring.log  # Log file path
     alerting:              # Alerting configuration
       enabled: true        # Enable alerting
       providers:           # Alert providers
         email:             # Email alerts
           enabled: true    # Enable email alerts
           smtp_server: smtp.example.com  # SMTP server
           smtp_port: 587   # SMTP port
           smtp_user: alerts@example.com  # SMTP username
           smtp_password: your-password  # SMTP password
           from_address: alerts@example.com  # From address
           to_addresses:    # To addresses
             - admin@example.com
             - ops@example.com
         slack:             # Slack alerts
           enabled: true    # Enable Slack alerts
           webhook_url: https://hooks.slack.com/services/...  # Webhook URL
           channel: "#alerts"  # Slack channel
     visualization:         # Visualization configuration
       enabled: true        # Enable visualization
       grafana:             # Grafana configuration
         url: http://localhost:3000  # Grafana URL
         api_key: your-api-key  # Grafana API key
         dashboard_path: /path/to/dashboards  # Path to dashboard definitions

Assistant Settings
~~~~~~~~~~~~~~~

Assistant settings control the behavior of the EGen-01 Assistant:

.. code-block:: yaml

   # Assistant settings
   assistant:
     enabled: true          # Enable assistant
     model: THL-150         # Model to use
     max_history: 10        # Maximum conversation history
     tools:                 # Available tools
       - name: web_search   # Web search tool
         enabled: true      # Enable web search
         api_key: your-api-key  # API key for search provider
       - name: calculator   # Calculator tool
         enabled: true      # Enable calculator
       - name: weather      # Weather tool
         enabled: true      # Enable weather
         api_key: your-api-key  # API key for weather provider
     personalization:       # Personalization settings
       enabled: true        # Enable personalization
       user_profiles: /path/to/profiles  # Path to user profiles
       learning_rate: 0.1   # Learning rate for personalization

Environment-Specific Configuration
-------------------------------

The EGen Platform supports environment-specific configuration files for different deployment environments.

Environment Detection
~~~~~~~~~~~~~~~~~

The environment is detected from the ``EGEN_ENV`` environment variable or the ``--env`` command-line argument. If neither is provided, it defaults to ``development``.

Environment-specific configuration files are loaded based on the detected environment:

.. code-block:: bash

   # Development environment
   config/egen.development.yml
   
   # Testing environment
   config/egen.testing.yml
   
   # Production environment
   config/egen.production.yml

Configuration Inheritance
~~~~~~~~~~~~~~~~~~~~~

Environment-specific configuration files inherit from the base configuration file (``config/egen.yml``) and override specific values:

.. code-block:: yaml

   # config/egen.yml (base configuration)
   environment: development
   
   logging:
     level: info
   
   api:
     port: 8000
   
   # config/egen.production.yml (production-specific configuration)
   environment: production
   
   logging:
     level: warning
   
   api:
     workers: 8

In this example, the production environment will use:

- ``environment: production`` (from production-specific configuration)
- ``logging.level: warning`` (from production-specific configuration)
- ``api.port: 8000`` (inherited from base configuration)
- ``api.workers: 8`` (from production-specific configuration)

Secret Management
--------------

The EGen Platform provides several methods for managing secrets securely.

Environment Variables
~~~~~~~~~~~~~~~~~

Sensitive information can be stored in environment variables:

.. code-block:: bash

   # Set secrets in environment
   export EGEN_SECRET_KEY="your-secret-key"
   export EGEN_DB_PASSWORD="your-db-password"
   export EGEN_API_KEY="your-api-key"

These values can be referenced in configuration files:

.. code-block:: yaml

   # Reference environment variables in configuration
   security:
     secret_key: ${EGEN_SECRET_KEY}
   
   database:
     uri: postgresql://user:${EGEN_DB_PASSWORD}@localhost:5432/egen
   
   api:
     key: ${EGEN_API_KEY}

Secret Files
~~~~~~~~~~

Sensitive information can be stored in separate files and loaded at runtime:

.. code-block:: yaml

   # Reference secret files in configuration
   security:
     secret_key_file: /run/secrets/egen_secret_key
   
   database:
     password_file: /run/secrets/egen_db_password
   
   api:
     key_file: /run/secrets/egen_api_key

The EGen Platform will read these files and use their contents as configuration values.

Vault Integration
~~~~~~~~~~~~~~

The EGen Platform can integrate with HashiCorp Vault for secret management:

.. code-block:: yaml

   # Vault configuration
   vault:
     enabled: true
     url: https://vault.example.com:8200
     token_file: /run/secrets/vault_token
     mount_point: secret
     secrets:
       - path: egen/database
         keys:
           - name: password
             config_path: database.password
       - path: egen/api
         keys:
           - name: key
             config_path: api.key

Configuration Validation
---------------------

The EGen Platform validates configuration at startup to ensure all required values are present and valid.

Schema Validation
~~~~~~~~~~~~~~

Configuration is validated against a JSON schema:

.. code-block:: python

   from egen.config import validate_config
   
   # Load and validate configuration
   try:
       config = validate_config("/path/to/config/egen.yml")
       print("Configuration is valid")
   except ValidationError as e:
       print(f"Configuration error: {e}")

Required Values
~~~~~~~~~~~~

Some configuration values are required and must be provided:

.. code-block:: yaml

   # Required values
   model:
     path: /path/to/models  # Required: Path to model files
   
   security:
     secret_key: your-secret-key  # Required: Secret key for JWT

Value Constraints
~~~~~~~~~~~~~~

Some configuration values have constraints:

.. code-block:: yaml

   # Value constraints
   api:
     port: 8000  # Must be between 1 and 65535
     workers: 4  # Must be positive integer
   
   model:
     temperature: 0.7  # Must be between 0 and 1
     batch_size: 4     # Must be positive integer

Configuration Best Practices
-------------------------

Follow these best practices for configuring the EGen Platform:

Separation of Concerns
~~~~~~~~~~~~~~~~~~

Separate configuration by concern:

.. code-block:: bash

   # Main configuration file
   config/egen.yml
   
   # Environment-specific configuration
   config/egen.development.yml
   config/egen.testing.yml
   config/egen.production.yml
   
   # Component-specific configuration
   config/database.yml
   config/model.yml
   config/security.yml

Version Control
~~~~~~~~~~~~

Manage configuration files in version control:

1. **Template Files**: Store template configuration files in version control
2. **Environment Variables**: Use environment variables for environment-specific values
3. **Secrets**: Keep secrets out of version control
4. **Documentation**: Document all configuration options

Example template file:

.. code-block:: yaml

   # config/egen.template.yml
   environment: ${EGEN_ENV:-development}
   
   logging:
     level: ${EGEN_LOG_LEVEL:-info}
   
   database:
     uri: postgresql://user:${EGEN_DB_PASSWORD}@${EGEN_DB_HOST:-localhost}:5432/egen

Documentation
~~~~~~~~~~~

Document all configuration options:

1. **Purpose**: Explain the purpose of each option
2. **Default Value**: Provide the default value
3. **Constraints**: Document any constraints or validation rules
4. **Examples**: Provide examples of valid values
5. **Related Options**: Document relationships between options

Regular Review
~~~~~~~~~~~

Regularly review and update configuration:

1. **Audit**: Regularly audit configuration for security issues
2. **Cleanup**: Remove unused or deprecated options
3. **Optimization**: Optimize configuration for performance
4. **Documentation**: Keep documentation up to date
5. **Testing**: Test configuration changes in non-production environments

Configuration Examples
-------------------

Development Environment
~~~~~~~~~~~~~~~~~~~

Configuration for a development environment:

.. code-block:: yaml

   # config/egen.development.yml
   environment: development
   debug: true
   
   logging:
     level: debug
     format: text
     output: stdout
   
   api:
     host: 127.0.0.1
     port: 8000
     workers: 1
     timeout: 60
     rate_limit: 0  # No rate limiting in development
   
   web:
     port: 8501
     theme: light
     api_url: http://localhost:8000
   
   database:
     uri: postgresql://user:password@localhost:5432/egen_dev
     echo: true  # Log SQL queries
   
   model:
     path: ./models
     default: THL-150
     quantization: none  # No quantization in development
   
   security:
     enable_auth: false  # No authentication in development
     secret_key: development-secret-key

Production Environment
~~~~~~~~~~~~~~~~~~

Configuration for a production environment:

.. code-block:: yaml

   # config/egen.production.yml
   environment: production
   debug: false
   
   logging:
     level: info
     format: json
     output: file
     file: /var/log/egen/api.log
     rotation: daily
     retention: 30
     compress: true
   
   api:
     host: 0.0.0.0
     port: 8000
     workers: 8
     timeout: 30
     rate_limit: 100
   
   web:
     port: 8501
     theme: light
     api_url: https://api.egen-platform.org
   
   database:
     uri: postgresql://user:${EGEN_DB_PASSWORD}@db.egen-platform.org:5432/egen_prod
     pool_size: 20
     max_overflow: 30
     echo: false
   
   model:
     path: /opt/egen/models
     default: THL-150
     quantization: int8
     batch_size: 8
   
   security:
     enable_auth: true
     auth_provider: jwt
     secret_key: ${EGEN_SECRET_KEY}
     token_expiry: 3600

High-Performance Environment
~~~~~~~~~~~~~~~~~~~~~~~~

Configuration for a high-performance environment:

.. code-block:: yaml

   # config/egen.high-performance.yml
   environment: production
   debug: false
   
   logging:
     level: warning  # Reduce logging overhead
     format: json
     output: file
     file: /var/log/egen/api.log
   
   api:
     host: 0.0.0.0
     port: 8000
     workers: 16  # More workers for higher throughput
     timeout: 60
     rate_limit: 200  # Higher rate limit
   
   database:
     uri: postgresql://user:${EGEN_DB_PASSWORD}@db.egen-platform.org:5432/egen_prod
     pool_size: 50  # Larger connection pool
     max_overflow: 50
   
   redis:
     uri: redis://redis.egen-platform.org:6379/0
     pool_size: 50  # Larger connection pool
   
   model:
     path: /opt/egen/models
     default: THL-150
     quantization: int8
     batch_size: 16  # Larger batch size
     cache_size: 5000  # Larger cache
     use_cuda_graphs: true
     optimize_for_inference: true
     use_flash_attention: true

Minimal Environment
~~~~~~~~~~~~~~~~

Configuration for a minimal environment with limited resources:

.. code-block:: yaml

   # config/egen.minimal.yml
   environment: production
   debug: false
   
   logging:
     level: warning
     format: text
     output: file
     file: /var/log/egen/api.log
   
   api:
     host: 0.0.0.0
     port: 8000
     workers: 2  # Fewer workers for lower resource usage
     timeout: 60
     rate_limit: 50  # Lower rate limit
   
   database:
     uri: postgresql://user:${EGEN_DB_PASSWORD}@localhost:5432/egen_prod
     pool_size: 5  # Smaller connection pool
     max_overflow: 10
   
   redis:
     uri: redis://localhost:6379/0
     pool_size: 5  # Smaller connection pool
   
   model:
     path: /opt/egen/models
     default: THL-150
     quantization: int8
     batch_size: 1  # Smaller batch size
     cache_size: 100  # Smaller cache

Configuration Troubleshooting
--------------------------

Common Issues
~~~~~~~~~~

**Missing Configuration File**

If the configuration file is missing, the EGen Platform will use default values or fail if required values are missing.

Solution:

.. code-block:: bash

   # Create configuration file from template
   cp config/egen.template.yml config/egen.yml
   
   # Edit configuration file
   nano config/egen.yml

**Invalid Configuration Values**

If configuration values are invalid, the EGen Platform will log errors and may fail to start.

Solution:

.. code-block:: bash

   # Validate configuration file
   python -m egen.config.validate config/egen.yml
   
   # Fix validation errors
   nano config/egen.yml

**Environment Variable Not Set**

If an environment variable referenced in the configuration is not set, the EGen Platform will use the default value or fail if no default is provided.

Solution:

.. code-block:: bash

   # Set environment variable
   export EGEN_SECRET_KEY="your-secret-key"
   
   # Verify environment variable
   echo $EGEN_SECRET_KEY

**Permission Issues**

If the EGen Platform cannot read the configuration file due to permission issues, it will fail to start.

Solution:

.. code-block:: bash

   # Check file permissions
   ls -l config/egen.yml
   
   # Fix file permissions
   chmod 644 config/egen.yml

Debugging Configuration
~~~~~~~~~~~~~~~~~~~

To debug configuration issues, use the following techniques:

**Print Configuration**

.. code-block:: python

   from egen.config import load_config
   
   # Load and print configuration
   config = load_config("/path/to/config/egen.yml")
   print(config)

**Check Environment Variables**

.. code-block:: bash

   # Print all EGEN environment variables
   env | grep EGEN

**Validate Configuration**

.. code-block:: bash

   # Validate configuration file
   python -m egen.config.validate config/egen.yml

**Enable Debug Logging**

.. code-block:: bash

   # Set debug log level
   export EGEN_LOG_LEVEL=debug
   
   # Start the application
   python -m egen.api.main

Configuration API Reference
------------------------

Configuration Module
~~~~~~~~~~~~~~~~

The ``egen.config`` module provides utilities for loading and managing configuration:

.. code-block:: python

   from egen.config import (
       load_config,
       get_config,
       validate_config,
       ConfigError
   )
   
   # Load configuration from file
   config = load_config("/path/to/config/egen.yml")
   
   # Get global configuration
   config = get_config()
   
   # Validate configuration
   try:
       validate_config("/path/to/config/egen.yml")
       print("Configuration is valid")
   except ConfigError as e:
       print(f"Configuration error: {e}")

Configuration Class
~~~~~~~~~~~~~~~

The ``Config`` class provides access to configuration values:

.. code-block:: python

   from egen.config import Config
   
   # Create configuration object
   config = Config({
       "api": {
           "port": 8000,
           "workers": 4
       },
       "database": {
           "uri": "postgresql://user:password@localhost:5432/egen"
       }
   })
   
   # Access configuration values
   api_port = config.api.port  # 8000
   db_uri = config.database.uri  # "postgresql://user:password@localhost:5432/egen"
   
   # Access with default value
   log_level = config.get("logging.level", default="info")  # "info"
   
   # Check if value exists
   has_redis = config.has("redis.uri")  # False
   
   # Set value
   config.set("api.timeout", 60)
   
   # Convert to dictionary
   config_dict = config.to_dict()

Configuration Command-Line Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The EGen Platform provides a command-line interface for managing configuration:

.. code-block:: bash

   # Validate configuration file
   python -m egen.config.validate config/egen.yml
   
   # Generate template configuration file
   python -m egen.config.generate --output config/egen.template.yml
   
   # Print current configuration
   python -m egen.config.print
   
   # Print specific configuration value
   python -m egen.config.print --path api.port
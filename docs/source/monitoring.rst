Monitoring & Analytics
====================

Overview
--------

The Monitoring & Analytics module provides comprehensive observability for the EGen platform. It collects metrics, logs, and traces to monitor system health, performance, and usage patterns, enabling real-time insights and alerting.

Architecture
-----------

.. code-block::

    Monitoring & Analytics
    ├── Metrics Collection
    │   ├── System Metrics
    │   ├── Model Metrics
    │   └── API Metrics
    ├── Logging System
    │   ├── Log Aggregation
    │   ├── Structured Logging
    │   └── Log Analysis
    ├── Alerting
    │   ├── Alert Rules
    │   ├── Notification Channels
    │   └── Alert Management
    └── Visualization
        ├── Dashboards
        ├── Reports
        └── Anomaly Detection

Components
---------

Metrics Collection
~~~~~~~~~~~~~~~~

The Metrics Collection component gathers performance and operational data:

- **System Metrics**: CPU, memory, disk, network usage
- **Model Metrics**: Inference time, token generation rate, model accuracy
- **API Metrics**: Request rate, latency, error rate, endpoint usage

Logging System
~~~~~~~~~~~~

The Logging System component manages log data:

- **Log Aggregation**: Collects logs from all system components
- **Structured Logging**: Standardizes log format for easier analysis
- **Log Analysis**: Parses logs for patterns, errors, and insights

Alerting
~~~~~~~

The Alerting component notifies about system issues:

- **Alert Rules**: Conditions that trigger notifications
- **Notification Channels**: Email, Slack, PagerDuty, etc.
- **Alert Management**: Alert grouping, silencing, and escalation

Visualization
~~~~~~~~~~~

The Visualization component presents monitoring data:

- **Dashboards**: Real-time system overview and detailed metrics
- **Reports**: Periodic summaries of system performance
- **Anomaly Detection**: Highlighting unusual patterns or behaviors

Technologies
-----------

The EGen monitoring stack uses the following technologies:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **Elasticsearch**: Log storage and search
- **Kibana**: Log visualization and analysis
- **AlertManager**: Alert routing and notification

API Reference
------------

Metrics Collection
~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.monitoring.metrics import MetricsCollector
    
    # Initialize metrics collector
    collector = MetricsCollector(
        prometheus_endpoint="http://localhost:9090"
    )
    
    # Record model inference metrics
    collector.record_inference(
        model_name="thl150",
        inference_time=0.856,
        input_tokens=25,
        output_tokens=150,
        domain="code"
    )
    
    # Record API request metrics
    collector.record_request(
        endpoint="/v1/generate",
        status_code=200,
        latency=0.923,
        user_id="user_123"
    )
    
    # Get current metrics
    metrics = collector.get_metrics()

Logging System
~~~~~~~~~~~~

.. code-block:: python

    from egen.monitoring.logging import Logger
    
    # Initialize logger
    logger = Logger(
        service_name="egen-api",
        log_level="INFO"
    )
    
    # Log events
    logger.info("API request received", extra={"endpoint": "/v1/generate", "user_id": "user_123"})
    logger.warning("High latency detected", extra={"latency": 2.5, "threshold": 1.0})
    logger.error("Model inference failed", extra={"error": "CUDA out of memory", "model": "thl150"})
    
    # Query logs
    logs = logger.query(
        service="egen-api",
        level="ERROR",
        time_range="1h"
    )

Alerting
~~~~~~~

.. code-block:: python

    from egen.monitoring.alerting import AlertManager
    
    # Initialize alert manager
    alert_manager = AlertManager(
        config_path="/path/to/alertmanager.yml"
    )
    
    # Define alert rule
    alert_manager.add_rule(
        name="high_error_rate",
        query="rate(api_errors_total[5m]) > 0.05",
        severity="critical",
        annotations={
            "summary": "High API error rate",
            "description": "Error rate exceeds 5% over 5 minutes"
        }
    )
    
    # Get active alerts
    alerts = alert_manager.get_alerts()
    
    # Silence an alert
    alert_manager.silence_alert(
        alert_id="alert_123",
        duration="2h",
        reason="Investigating issue"
    )

Visualization
~~~~~~~~~~~

.. code-block:: python

    from egen.monitoring.visualization import DashboardManager
    
    # Initialize dashboard manager
    dashboard_manager = DashboardManager(
        grafana_url="http://localhost:3000",
        grafana_api_key="YOUR_API_KEY"
    )
    
    # Create dashboard
    dashboard_id = dashboard_manager.create_dashboard(
        title="EGen API Performance",
        panels=[
            {"title": "Request Rate", "query": "rate(api_requests_total[5m])"}, 
            {"title": "Latency", "query": "histogram_quantile(0.95, sum(rate(api_latency_bucket[5m])) by (le))"}
        ]
    )
    
    # Get dashboard URL
    dashboard_url = dashboard_manager.get_dashboard_url(dashboard_id)

Configuration
-------------

Prometheus Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    # prometheus.yml
    
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    alerting:
      alertmanagers:
        - static_configs:
            - targets: ['alertmanager:9093']
    
    rule_files:
      - "alerts.yml"
    
    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']
      
      - job_name: 'egen_model'
        static_configs:
          - targets: ['egen-model:8000']
        metrics_path: '/metrics'
      
      - job_name: 'node_exporter'
        static_configs:
          - targets: ['node-exporter:9100']

Grafana Dashboard
~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "dashboard": {
        "id": null,
        "title": "EGen Platform",
        "tags": ["egen", "ai"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Inference Request Rate",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
              {
                "expr": "sum(rate(model_inference_requests_total[5m]))",
                "legendFormat": "Requests/sec"
              }
            ]
          },
          {
            "title": "Inference Latency (p95)",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, sum(rate(model_inference_latency_bucket[5m])) by (le))",
                "legendFormat": "p95 Latency"
              }
            ]
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
              {
                "expr": "sum(rate(api_errors_total[5m])) / sum(rate(api_requests_total[5m]))",
                "legendFormat": "Error Rate"
              }
            ]
          },
          {
            "title": "CPU Usage",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
              {
                "expr": "sum(rate(process_cpu_seconds_total[5m])) * 100",
                "legendFormat": "CPU %"
              }
            ]
          }
        ]
      }
    }

Usage Examples
-------------

Basic Monitoring Setup
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.monitoring import setup_monitoring
    
    # Setup monitoring for a FastAPI application
    app = FastAPI()
    
    # Add monitoring middleware
    setup_monitoring(
        app,
        service_name="egen-api",
        metrics_endpoint="/metrics",
        log_level="INFO"
    )
    
    # Routes will be automatically monitored
    @app.post("/v1/generate")
    async def generate(request: GenerateRequest):
        # Function implementation
        pass

Custom Metrics
~~~~~~~~~~~~

.. code-block:: python

    from egen.monitoring.metrics import counter, gauge, histogram
    
    # Define custom metrics
    inference_requests = counter(
        name="model_inference_requests_total",
        description="Total number of model inference requests",
        labels=["model", "domain"]
    )
    
    model_memory_usage = gauge(
        name="model_memory_usage_bytes",
        description="Current memory usage of the model",
        labels=["model"]
    )
    
    inference_latency = histogram(
        name="model_inference_latency_seconds",
        description="Model inference latency in seconds",
        labels=["model", "domain"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
    )
    
    # Use metrics in code
    def process_inference_request(model_name, domain, input_text):
        inference_requests.inc(labels={"model": model_name, "domain": domain})
        
        start_time = time.time()
        result = model.generate(input_text)
        latency = time.time() - start_time
        
        inference_latency.observe(
            value=latency,
            labels={"model": model_name, "domain": domain}
        )
        
        model_memory_usage.set(
            value=get_model_memory_usage(model_name),
            labels={"model": model_name}
        )
        
        return result

Log Analysis
~~~~~~~~~~

.. code-block:: python

    from egen.monitoring.logging import LogAnalyzer
    
    # Initialize log analyzer
    analyzer = LogAnalyzer(
        elasticsearch_url="http://elasticsearch:9200",
        index_pattern="egen-*"
    )
    
    # Find error patterns
    error_patterns = analyzer.find_patterns(
        query="level:ERROR",
        time_range="24h",
        group_by="error_type"
    )
    
    # Get error frequency over time
    error_frequency = analyzer.get_frequency(
        query="level:ERROR",
        time_range="24h",
        interval="1h"
    )
    
    # Find correlated events
    correlated_events = analyzer.find_correlations(
        query="message:*latency*",
        time_range="24h",
        correlation_window="5m"
    )